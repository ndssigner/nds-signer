#!/usr/bin/env python3
"""Extract SeedSigner's Screen API: for every class in gui/screens/*.py (and
gui/components.py ButtonOption), its dataclass fields including inherited
ones, in order, with defaults. Used to keep NDS-Signer's native screens
call-compatible with the upstream views (tests/host: screen-api check).

    tools/screen_api.py third_party/seedsigner/src [ClassName ...]
"""
import ast
import pathlib
import sys


def load(src_root):
    classes = {}
    for path in sorted((src_root / "seedsigner/gui").rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            fields = []
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    ann = ast.unparse(stmt.annotation)
                    if ann.startswith("ClassVar"):
                        continue
                    default = ast.unparse(stmt.value) if stmt.value is not None else None
                    fields.append((stmt.target.id, default))
            bases = [ast.unparse(b) for b in node.bases]
            classes[node.name] = {"bases": bases, "fields": fields,
                                  "module": str(path.relative_to(src_root))}
    return classes


def all_fields(classes, name, seen=None):
    info = classes.get(name)
    if info is None:
        return []
    out = []
    for base in info["bases"]:
        base = base.split(".")[-1]
        for f in all_fields(classes, base):
            if f[0] not in [o[0] for o in out]:
                out.append(f)
    for f in info["fields"]:
        out = [o for o in out if o[0] != f[0]] + [f]
    return out


def main():
    root = pathlib.Path(sys.argv[1])
    classes = load(root)
    names = sys.argv[2:] or sorted(classes)
    for name in names:
        info = classes[name]
        fields = all_fields(classes, name)
        print("%s(%s)  [%s]" % (name, ", ".join(info["bases"]), info["module"]))
        for fname, default in fields:
            print("    %s = %s" % (fname, default))


if __name__ == "__main__":
    main()
