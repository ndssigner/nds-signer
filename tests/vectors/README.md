# QR test vectors

Payloads used to test QR scanning and type detection. Generate a camera image
for melonDS with `tools/qr_to_png.py` (see its `--help`).

| File | QR type | Source |
| :--- | :--- | :--- |
| `psbt_base64_singlesig.txt` | `PSBT__BASE64` (testnet) | SeedSigner `tests/test_decodepsbtqr.py` (MIT) |
| `address_testnet.txt` | `BITCOIN_ADDRESS` | SeedSigner test suite (MIT) |
| `seedqr_12words.txt` | `SEED__SEEDQR` | SeedSigner test suite (MIT) |
| `psbt_base64_singlesig.mnemonic.txt` | Test seed that signs the PSBT above (fingerprint `8b218e81`) | SeedSigner `tests/test_decodepsbtqr.py` (MIT) |
| `psbt_base64_singlesig.signed.txt` | Expected result of signing it with embit 0.8.0 (RFC 6979, deterministic) | Generated with embit 0.8.0 |
| `psbt_base64_10in.*` | Synthetic 10-input P2WPKH testnet PSBT (made-up prevouts), public seed "abandon ... about"; `.summary.txt` / `.signed.txt` are the CPython references | `tools/make_test_psbt.py` |
| `psbt_base64_singlesig.summary.txt` | SeedSigner `PSBTParser` summary on CPython (reference) | `psbt_parser_summary.py` |
| `psbt_parser_summary.py` | Helper that prints the summary, identical on CPython and the DSi | NDS-Signer |
| `passphrase.txt`, `passphrase.fingerprint.txt` | Test BIP-39 passphrase for the singlesig seed and the resulting fingerprint (SeedSigner on CPython) | NDS-Signer |
| `seedqr_12words.fingerprint.txt` | Fingerprint of the SeedQR seed (SeedSigner on CPython) | NDS-Signer |
| `*.signed_trimmed.txt` | Signed and trimmed PSBT, as SeedSigner's PSBTFinalizeView outputs it | `tools/make_trimmed_ref.py` |
| `*.ur.txt` | Animated UR parts of the PSBT (SeedSigner's own encoder) | `tools/make_ur_parts.py` |
| `psbt_base64_singlesig.seedqr.txt` | SeedQR (standard) of the singlesig test seed, fingerprint `8b218e81` | NDS-Signer (BIP-39 word indexes) |
| `bip39_japanese.json` | Official Japanese BIP-39 test vectors | [bip32JP](https://github.com/bip32JP/bip32JP.github.io) |
| `passphrase_es.*` | Non-ASCII passphrase and resulting fingerprint (SeedSigner on CPython) | NDS-Signer |
| `plain_text.txt` | `INVALID` (not a Bitcoin payload) | NDS-Signer |

All keys and seeds here are public test data. **Never put real funds on them.**
