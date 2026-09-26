#!/usr/bin/env python3
"""Adapt vendored MicroPython user C modules written for MicroPython ~v1.19
(diybitcoinhardware: uhashlib from f469-disco, secp256k1-embedded) to the
MicroPython API used by NDS-Signer.

Idempotent: run it again after re-vendoring upstream files.
    tools/port_mpy_usermod.py lib/mpy-usermods/uhashlib lib/mpy-usermods/secp256k1
"""
import pathlib
import re
import sys

TYPE_RE = re.compile(
    r"static const mp_obj_type_t (\w+) = \{\s*\{ &mp_type_type \},\s*"
    r"\.name = (MP_QSTR_\w+),\s*\.make_new = (\w+),\s*"
    r"\.locals_dict = \(void\*\)&(\w+),\s*\};",
    re.S,
)
MODULE_RE = re.compile(r"MP_REGISTER_MODULE\((MP_QSTR_\w+), (\w+), (\w+)\);")


def port(src: str) -> str:
    src = re.sub(r"\bSTATIC\b", "static", src)
    src = re.sub(r"m_new_obj_var\((\w+), char, ", r"m_new_obj_var(\1, state, char, ", src)
    src = TYPE_RE.sub(
        r"MP_DEFINE_CONST_OBJ_TYPE(\n    \1, \2, MP_TYPE_FLAG_NONE,\n"
        r"    make_new, \3,\n    locals_dict, &\4\n    );",
        src,
    )
    src = MODULE_RE.sub(r"#if \3\nMP_REGISTER_MODULE(\1, \2);\n#endif", src)
    src = re.sub(r'mp_raise_ValueError\("([^"]*)"\)', r'mp_raise_ValueError(MP_ERROR_TEXT("\1"))', src)
    src = re.sub(r'mp_raise_TypeError\("([^"]*)"\)', r'mp_raise_TypeError(MP_ERROR_TEXT("\1"))', src)
    src = re.sub(r"mp_obj_new_str_from_vstr\(&mp_type_bytes, ", "mp_obj_new_bytes_from_vstr(", src)
    src = port_secp256k1(src)
    return src


def port_secp256k1(src):
    """secp256k1-embedded (2021) -> libsecp256k1 v0.8 API."""
    if "secp256k1_context_preallocated_create" not in src:
        return src
    # removed deprecated names: privkey_* -> seckey_*, schnorrsig_sign -> sign32
    src = re.sub(r"(?<![u\w])secp256k1_ec_privkey_(negate|tweak_add|tweak_mul)\(",
                 r"secp256k1_ec_seckey_\1(", src)
    src = re.sub(r"(?<![u\w])secp256k1_schnorrsig_sign\(", "secp256k1_schnorrsig_sign32(", src)
    # The context size was hard-coded ("880 // 440 for 32-bit. FIXME:
    # autodetect"): a larger context in a newer library would overflow it.
    src = src.replace(
        "#define PREALLOCATED_CTX_SIZE 880 // 440 for 32-bit. FIXME: autodetect",
        "// NDS-Signer: generous buffer, size checked at runtime (maybe_init_ctx)\n"
        "#define PREALLOCATED_CTX_SIZE 2048")
    src = src.replace(
        "    ctx = secp256k1_context_preallocated_create((void *)preallocated_ctx, "
        "SECP256K1_CONTEXT_VERIFY | SECP256K1_CONTEXT_SIGN);",
        "    if (secp256k1_context_preallocated_size(SECP256K1_CONTEXT_NONE) > PREALLOCATED_CTX_SIZE) {\n"
        "        mp_raise_msg(&mp_type_RuntimeError, MP_ERROR_TEXT(\"secp256k1 context buffer too small\"));\n"
        "    }\n"
        "    ctx = secp256k1_context_preallocated_create((void *)preallocated_ctx, SECP256K1_CONTEXT_NONE);")
    return src


def main():
    for root in map(pathlib.Path, sys.argv[1:]):
        for path in sorted(root.glob("*.c")):
            path.write_text(port(path.read_text()))
            print("ported", path)


if __name__ == "__main__":
    main()
