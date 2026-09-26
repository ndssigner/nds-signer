# NDS-Signer overlay for SeedSigner

Python modules that replace (or add to) upstream `seedsigner` modules at build
time. Everything else in the frozen `seedsigner` package is upstream code
(`third_party/seedsigner`, transformed by `tools/upy_transform.py`).

| Module | Replaces | Why |
| :--- | :--- | :--- |
| `gui/` | upstream `gui/` (Pillow, 240x240 joystick UI) | native dual-screen touch UI over the `nds` module; screen classes keep upstream names and keyword arguments (generated `gui/_upstream.py`) |
| `hardware/` | Raspberry Pi drivers | DSi camera/keys are native (`nds`) |
| `views/screensaver.py` | Pillow splash/screensaver | no Pillow |
| `helpers/qr.py` | `qrcode` + Pillow QR images | QR codes are drawn natively |
