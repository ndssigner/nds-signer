# 🗝️ NDS-Signer

> **Turn a $30 Nintendo DSi into a 100% Air-Gapped, Stateless Bitcoin Hardware Wallet.**

NDS-Signer is an open-source homebrew application (`.nds`) that transforms retro handheld consoles into a secure, offline Bitcoin PSBT signer. Built on the security principles of [SeedSigner](https://github.com/SeedSigner/seedsigner), NDS-Signer brings air-gapped cryptographic signing to widely available, low-cost hardware using a dual-screen stylus UI.

---

## 📸 Demo

*(Insert a 15-second video/GIF here showing the DSi scanning a PSBT QR from a laptop screen and outputting the signed QR code on the top LCD).*

---

## 🛡️ Security Philosophy & Threat Model

NDS-Signer is designed for maximum physical security, privacy, and plausible deniability.

### Key Guiding Principles
* **100% Air-Gapped:** Zero networking code initialized. The application never loads Wi-Fi drivers or attempts any outbound connections.
* **Stateless & Ephemeral:** Private keys and seeds reside **strictly in RAM**. When you turn off the console, all cryptographic material instantly vanishes. Nothing is ever written to the SD card or internal flash memory.
* **No Closed-Source TRNG:** We do not trust closed-source hardware random number generators. Seed generation relies entirely on user-provided entropy (BIP-39 dice rolls and camera noise).
* **Camouflage & Plausible Deniability:** A retro Nintendo console stored in a drawer looks like a 15-year-old toy, not a Bitcoin vault. When combined with a BIP-39 passphrase, entering a decoy PIN unveils a decoy wallet with zero cryptographic proof of a real wallet's existence.

---

## 🕹️ Why Nintendo Handhelds?

| Feature | NDS-Signer (Nintendo DSi) | DIY Raspberry Pi Signers |
| :--- | :--- | :--- |
| **Cost** | ~$20 - $40 (used market) | ~$50 - $70 (parts + shipping) |
| **Availability** | 200M+ units manufactured globally | Subject to Pi supply shortages |
| **Form Factor** | All-in-one (Dual screen, camera, battery) | Requires assembling custom cases |
| **Input Method** | Touchscreen + Stylus (Fast passphrase typing) | Single joystick / d-pad navigation |
| **Supply Chain Risk** | Extremely low (Purchased as a used toy) | Medium (Interception during shipping) |

---

## 🔄 PSBT Signing Flow

1. **Craft Transaction:** Build a PSBT (Partially Signed Bitcoin Transaction) in your watch-only coordinator wallet (Sparrow, Electrum, Specter).
2. **Scan PSBT:** Open NDS-Signer on your console, enter your passphrase via the bottom touchscreen, and point the top screen camera at the coordinator's QR code.
3. **Review & Sign:** Verify transaction details (amount, recipient address, fee) on the dual screen and confirm signing.
4. **Broadcast:** Scan the animated signed PSBT QR code displayed on the console's top screen using your computer/phone coordinator.
5. **Power Off:** Shut down the console. All keys are wiped from memory.

---

## 🛠️ Reproducible Build Instructions (Docker)

To eliminate dependency issues and guarantee reproducible builds bit-for-bit, compilation is handled inside a containerized `devkitARM` environment.

### Prerequisites
* [Docker Desktop](https://www.docker.com/) installed on your machine.
* Git.

### Compiling the `.nds` Binary

```bash
# 1. Clone the repository
git clone [https://github.com/your-username/nds-signer.git](https://github.com/your-username/nds-signer.git)
cd nds-signer

# 2. Build the Docker compiler image
docker build -t nds-signer-builder .

# 3. Compile the application
docker run --rm -v $(pwd):/source nds-signer-builder make

# 4. Verify output
# The compiled `nds-signer.nds` binary will be available in the root folder.
# Verify the SHA-256 hash against the release signature:
sha256sum nds-signer.nds

```

---

## 🎮 Installation on Console

1. Format a MicroSD card to **FAT32**.
2. Install **TWiLight Menu++** on your Nintendo DSi or 3DS (see [dsi.cfw.guide](https://dsi.cfw.guide/?utm_source=gemini)).
3. Copy `nds-signer.nds` anywhere on your SD card.
4. Boot your console, launch TWiLight Menu++, and open `nds-signer.nds`.
5. *(Optional but recommended)* Delete all saved Wi-Fi profiles in the native Nintendo System Settings before entering seeds.

---

## 🚀 Good First Issues (We Need Your Help!)

We welcome contributions from C developers, homebrew enthusiasts, cypherpunks, and UI designers! Check out these beginner-friendly tasks:

* [ ] **[UI] Touchscreen Keyboard Layout (`#101`):** Implement a full QWERTY layout with shift/symbol toggles using `libnds` touch input.
* [ ] **[Camera] Frame Buffer Optimization (`#102`):** Optimize DSi camera capture frames for faster parsing with `quirc`.
* [ ] **[Crypto] BIP-39 Dice Roll Entropy UI (`#103`):** Create a visual interface for inputting 50-100 physical dice rolls to derive the root seed.
* [ ] **[QR] Animated QR Display (`#104`):** Implement multi-part (UR / Fountain) animated QR code rendering for large PSBT transactions.

---

## 📜 License & Disclaimer

This project is licensed under the **MIT License**.

*Disclaimer: NDS-Signer is experimental software provided "as is" without warranty of any kind. Always test with small amounts or on Bitcoin Testnet/Signet before using with mainnet funds.*
