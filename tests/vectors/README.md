# QR test vectors

Payloads used to test QR scanning and type detection. Generate a camera image
for melonDS with `tools/qr_to_png.py` (see its `--help`).

| File | QR type | Source |
| :--- | :--- | :--- |
| `psbt_base64_singlesig.txt` | `PSBT__BASE64` (testnet) | SeedSigner `tests/test_decodepsbtqr.py` (MIT) |
| `address_testnet.txt` | `BITCOIN_ADDRESS` | SeedSigner test suite (MIT) |
| `seedqr_12words.txt` | `SEED__SEEDQR` | SeedSigner test suite (MIT) |
| `plain_text.txt` | `INVALID` (not a Bitcoin payload) | NDS-Signer |

All keys and seeds here are public test data. **Never put real funds on them.**
