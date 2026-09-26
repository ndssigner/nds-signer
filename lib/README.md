# Vendored third-party code

Copied unmodified from upstream so builds need no network access and every
line that ends up in the binary is reviewable in this repository.

| Directory | Project | License | Upstream commit |
| :--- | :--- | :--- | :--- |
| `quirc/` | [dlbeer/quirc](https://github.com/dlbeer/quirc) (`lib/` + `LICENSE`) | ISC | `927d680904dc95fdff4cd9d022eb374b438ff8f2` |
| `mpy-usermods/uhashlib/` | `usermods/uhashlib` from [diybitcoinhardware/f469-disco](https://github.com/diybitcoinhardware/f469-disco) (hashlib with sha512/ripemd160/pbkdf2, hmac); crypto from trezor-crypto | MIT (f469-disco), MIT/BSD-3 (crypto files, see headers) | `9dd8515` — **modified**, see below |
| `mpy-usermods/secp256k1/` | `mpy/` wrapper from [diybitcoinhardware/secp256k1-embedded](https://github.com/diybitcoinhardware/secp256k1-embedded) | MIT | `036f465` — **modified**, see below |
| `../tools/third_party/qrcodegen.py` | [nayuki/QR-Code-generator](https://github.com/nayuki/QR-Code-generator) (host tool only) | MIT | `3c6d0b3cefb4e049dc337e82237c9644399716a8` |

Git submodules (pinned, in `third_party/`): MicroPython `v1.29.0`, embit
`v0.8.0` (the version SeedSigner pins), libsecp256k1 `be8d9c2` (the commit
secp256k1-embedded is tested with).

### Modifications to vendored code

- `mpy-usermods/*/*.c`: adapted from the MicroPython ~v1.19 C API to v1.29 by
  `tools/port_mpy_usermod.py` (mechanical, re-runnable after re-vendoring).
- `mpy-usermods/secp256k1/config/ecmult_static_context.h`: includes the table
  generated at build time by libsecp256k1's own `gen_context` instead of the
  pre-generated 217 KB copy (identical data, verified).

Build-time configuration (see `arm9/Makefile`): quirc is compiled with
`QUIRC_FLOAT_TYPE=float` and `QUIRC_USE_TGMATH`, because the ARM9 has no FPU.

To update, replace the files with the new upstream version, update the commit
above and review the diff.
