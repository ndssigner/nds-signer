#!/usr/bin/env python3
"""Build-time source transform: upstream CPython code -> MicroPython.

Reads unmodified upstream Python (e.g. SeedSigner, from its pinned submodule)
and writes an equivalent, readable copy that MicroPython can run. Only
constructs MicroPython cannot support are rewritten:

  * @dataclass classes: MicroPython discards class annotations, so annotated
    fields are recorded in order in `__nds_fields__` and annotation-only lines
    are removed. The runtime shim (mpy/frozen/compat/dataclasses.py) builds
    __init__ from that list.
  * Annotated assignments in class bodies become plain assignments.
  * Subscripted generic bases (PEP 585), e.g. `class BackStack(list[X])`,
    become the plain type (`list`): identical at runtime, unsupported by
    MicroPython.
  * `cls.__new__(cls)` (SeedSigner's singletons) becomes
    `object.__new__(cls)`: MicroPython classes do not expose `__new__`. Only
    equivalent when no class defines its own `__new__`, which is checked.
  * f-strings become the equivalent "...".format(...) calls: MicroPython's
    f-string support is limited (e.g. no nested quotes, PEP 701).
  * With --ordered-dicts (used for urtypes): dict displays and comprehensions
    become collections.OrderedDict. CPython dicts keep insertion order,
    MicroPython's do not; urtypes' CBOR encoder writes maps in iteration order,
    so without this its output bytes differ from SeedSigner's on CPython.
  * With --no-new-rewrite: skip the __new__ rewrite (for code that defines
    its own __new__, e.g. urtypes).
  * str methods MicroPython lacks become calls to equivalents in
    mpy/frozen/compat/nds_strcompat.py (STR_METHODS), e.g. s.zfill(8) ->
    _nds_zfill(s, 8).
  * Builtin names MicroPython lacks are replaced (NAME_REPLACEMENTS), e.g.
    UnicodeDecodeError -> UnicodeError (what MicroPython's bytes.decode()
    raises on invalid UTF-8).
  * IMPORT_REPLACEMENTS: per-module `import X` -> `import Y as X`. Used to
    give one module something a global replacement must not provide (see
    the table).

Everything else is emitted as-is (via ast.unparse, so comments are dropped).

Usage:
    tools/upy_transform.py --src third_party/seedsigner/src --out build/frozen_py \\
        seedsigner/models/psbt_parser.py ...
"""
import argparse
import ast
import pathlib
import sys


def is_dataclass_decorator(node):
    target = node.func if isinstance(node, ast.Call) else node
    return (isinstance(target, ast.Name) and target.id == "dataclass") or (
        isinstance(target, ast.Attribute) and target.attr == "dataclass"
    )


ORDERED_DICT = "_nds_OrderedDict"


class Transformer(ast.NodeTransformer):
    def __init__(self, ordered_dicts=False, rewrite_new=True):
        self.ordered_dicts = ordered_dicts
        self.rewrite_new = rewrite_new
        self.used_ordered_dict = False

    def visit_Dict(self, node):
        self.generic_visit(node)
        if not self.ordered_dicts or any(k is None for k in node.keys):  # {**x}: keep
            return node
        self.used_ordered_dict = True
        pairs = ast.List(elts=[ast.Tuple(elts=[k, v], ctx=ast.Load())
                               for k, v in zip(node.keys, node.values)], ctx=ast.Load())
        return ast.copy_location(ast.Call(func=ast.Name(id=ORDERED_DICT, ctx=ast.Load()),
                                          args=[pairs], keywords=[]), node)

    def visit_DictComp(self, node):
        self.generic_visit(node)
        if not self.ordered_dicts:
            return node
        self.used_ordered_dict = True
        gen = ast.GeneratorExp(elt=ast.Tuple(elts=[node.key, node.value], ctx=ast.Load()),
                               generators=node.generators)
        return ast.copy_location(ast.Call(func=ast.Name(id=ORDERED_DICT, ctx=ast.Load()),
                                          args=[gen], keywords=[]), node)

    def visit_FunctionDef(self, node):
        if node.name == "__new__" and self.rewrite_new:
            raise SystemExit("upy_transform: custom __new__ found; the __new__ rewrite "
                             "would be wrong for it (line %d)" % node.lineno)
        self.generic_visit(node)
        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        func = node.func
        if self.rewrite_new and isinstance(func, ast.Attribute) and func.attr == "__new__" and not (
                isinstance(func.value, ast.Name) and func.value.id == "object"):
            node.func = ast.Attribute(value=ast.Name(id="object", ctx=ast.Load()),
                                      attr="__new__", ctx=ast.Load())
        return node

    def visit_JoinedStr(self, node):
        template, args = "", []
        for part in node.values:
            if isinstance(part, ast.Constant):
                template += part.value.replace("{", "{{").replace("}", "}}")
                continue
            part.value = self.visit(part.value)
            field = "{"
            if part.conversion != -1:
                field += "!" + chr(part.conversion)
            if part.format_spec is not None:
                spec = part.format_spec
                if not all(isinstance(v, ast.Constant) for v in spec.values):
                    raise SystemExit("upy_transform: dynamic f-string format spec (line %d)"
                                     % node.lineno)
                field += ":" + "".join(v.value for v in spec.values)
            template += field + "}"
            args.append(part.value)
        if not args:
            return ast.copy_location(ast.Constant(template.replace("{{", "{").replace("}}", "}")), node)
        call = ast.Call(func=ast.Attribute(value=ast.Constant(template), attr="format", ctx=ast.Load()),
                        args=args, keywords=[])
        return ast.copy_location(call, node)

    def visit_ClassDef(self, node):
        self.generic_visit(node)
        node.bases = [b.value if isinstance(b, ast.Subscript) else b for b in node.bases]
        is_dc = any(is_dataclass_decorator(d) for d in node.decorator_list)
        fields = []
        body = []
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                name = stmt.target.id
                ann = ast.unparse(stmt.annotation)
                if is_dc and not ann.startswith("ClassVar"):
                    fields.append(name)
                if stmt.value is not None:
                    body.append(ast.copy_location(
                        ast.Assign(targets=[stmt.target], value=stmt.value), stmt))
                continue
            body.append(stmt)
        if is_dc:
            has_doc = body and isinstance(body[0], ast.Expr) and isinstance(
                getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str)
            body.insert(1 if has_doc else 0, ast.Assign(
                targets=[ast.Name(id="__nds_fields__", ctx=ast.Store())],
                value=ast.Tuple(elts=[ast.Constant(f) for f in fields], ctx=ast.Load()),
            ))
        if not body:
            body = [ast.Pass()]
        node.body = body
        return node


HEADER = (
    "# GENERATED by tools/upy_transform.py from upstream source: {src}\n"
    "# Do not edit; change the transform or the upstream pin instead.\n"
)


# rel path -> {module imported: module used instead}
IMPORT_REPLACEMENTS = {
    # The backup test picks which word to ask and shuffles decoy words with
    # `random`. NDS-Signer's global `random` refuses to work (no PRNG may
    # ever feed key material, e.g. embit's key helpers); this view gets a
    # non-cryptographic generator meant only for that (mpy/frozen/nds_ui_random.py).
    "seedsigner/views/seed_views.py": {"random": "nds_ui_random"},
}


# str methods missing in MicroPython -> function in nds_strcompat
STR_METHODS = {"zfill": "_nds_zfill"}


# builtins missing in MicroPython -> the one it provides instead
NAME_REPLACEMENTS = {"UnicodeDecodeError": "UnicodeError", "UnicodeEncodeError": "UnicodeError"}


class NameReplacer(ast.NodeTransformer):
    def visit_Name(self, node):
        if node.id in NAME_REPLACEMENTS:
            node.id = NAME_REPLACEMENTS[node.id]
        return node


class StrMethodRewriter(ast.NodeTransformer):
    def __init__(self):
        self.used = set()

    def visit_Call(self, node):
        self.generic_visit(node)
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in STR_METHODS and not node.keywords:
            name = STR_METHODS[func.attr]
            self.used.add(func.attr)
            return ast.copy_location(ast.Call(func=ast.Name(id=name, ctx=ast.Load()),
                                              args=[func.value] + node.args, keywords=[]), node)
        return node


class ImportReplacer(ast.NodeTransformer):
    def __init__(self, table):
        self.table = table

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in self.table:
                alias.asname = alias.asname or alias.name
                alias.name = self.table[alias.name]
        return node


def transform(path: pathlib.Path, rel: str, ordered_dicts=False, rewrite_new=True) -> str:
    tree = ast.parse(path.read_text(), filename=str(path))
    if rel in IMPORT_REPLACEMENTS:
        tree = ImportReplacer(IMPORT_REPLACEMENTS[rel]).visit(tree)
    tree = NameReplacer().visit(tree)
    str_methods = StrMethodRewriter()
    tree = str_methods.visit(tree)
    transformer = Transformer(ordered_dicts, rewrite_new)
    tree = transformer.visit(tree)
    for method in sorted(str_methods.used):
        tree.body.insert(0, ast.ImportFrom(module="nds_strcompat",
                                           names=[ast.alias(name=method, asname=STR_METHODS[method])],
                                           level=0))
    if transformer.used_ordered_dict:
        # after a module docstring / __future__ imports, before any other code
        index = 0
        while index < len(tree.body) and (
                (isinstance(tree.body[index], ast.Expr) and isinstance(getattr(tree.body[index], "value", None), ast.Constant))
                or (isinstance(tree.body[index], ast.ImportFrom) and tree.body[index].module == "__future__")):
            index += 1
        tree.body.insert(index, ast.ImportFrom(module="collections",
                                               names=[ast.alias(name="OrderedDict", asname=ORDERED_DICT)],
                                               level=0))
    ast.fix_missing_locations(tree)
    return HEADER.format(src=rel) + ast.unparse(tree) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    ap.add_argument("--ordered-dicts", action="store_true")
    ap.add_argument("--no-new-rewrite", action="store_true")
    ap.add_argument("files", nargs="+")
    args = ap.parse_args()
    opts = dict(ordered_dicts=args.ordered_dicts, rewrite_new=not args.no_new_rewrite)

    for rel in args.files:
        src = args.src / rel
        dst = args.out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(transform(src, rel, **opts))
        # make every directory a package, as upstream relies on implicit ones
        for parent in dst.parents:
            if parent == args.out or args.out not in parent.parents and parent != args.out:
                break
            init = parent / "__init__.py"
            if not init.exists():
                upstream_init = args.src / parent.relative_to(args.out) / "__init__.py"
                init.write_text(
                    transform(upstream_init, str(parent.relative_to(args.out) / "__init__.py"), **opts)
                    if upstream_init.exists() else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
