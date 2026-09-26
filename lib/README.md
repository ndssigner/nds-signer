# Vendored third-party code

Copied unmodified from upstream so builds need no network access and every
line that ends up in the binary is reviewable in this repository.

| Directory | Project | License | Upstream commit |
| :--- | :--- | :--- | :--- |
| `quirc/` | [dlbeer/quirc](https://github.com/dlbeer/quirc) (`lib/` + `LICENSE`) | ISC | `927d680904dc95fdff4cd9d022eb374b438ff8f2` |
| `../tools/third_party/qrcodegen.py` | [nayuki/QR-Code-generator](https://github.com/nayuki/QR-Code-generator) (host tool only) | MIT | `3c6d0b3cefb4e049dc337e82237c9644399716a8` |

Build-time configuration (see `arm9/Makefile`): quirc is compiled with
`QUIRC_FLOAT_TYPE=float` and `QUIRC_USE_TGMATH`, because the ARM9 has no FPU.

To update, replace the files with the new upstream version, update the commit
above and review the diff.
