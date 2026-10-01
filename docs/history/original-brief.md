> **Historical document.** The brief NDS-Signer started from (2026-09-26).
> The plan changed: SeedSigner is run unmodified through MicroPython instead
> of being ported to C, and only the DSi is supported. See
> [how-it-was-built.md](../how-it-was-built.md).

# Project Name: NDS-Signer (Air-Gapped Bitcoin PSBT Signer for Nintendo DS/DSi/3DS)

## 1. Project Overview
The goal is to build an open-source, stateless, and fully air-gapped Bitcoin hardware wallet / PSBT signer that runs as a homebrew `.nds` executable on Nintendo DSi and 3DS consoles.
The application will mimic the functionality and security model of "SeedSigner", but leveraging the dual screens, touchscreen, and camera of the Nintendo DS architecture.

**CRITICAL DIRECTIVE:** Do not reinvent the wheel. The core logic, UI flows, PSBT parsing, and cryptographic workflows MUST be directly ported or heavily adapted from the original open-source SeedSigner codebase. Rely on their proven architecture and translate it into C/C++ rather than designing custom implementations from scratch.

## 2. Security Constraints (CRITICAL)
- **Zero Networking:** The software must NEVER initialize or interact with the Wi-Fi hardware. It must remain strictly air-gapped.
- **Stateless Operation:** No private keys, seeds, or PSBT data can be written to the SD card or any non-volatile memory. All cryptographic operations must occur in RAM and vanish upon power off.
- **No External RNG:** Do not rely on hardware PRNG. Entropy for seeds will be generated purely by the user (BIP-39 dice rolls) and physical inputs.

## 3. Tech Stack & Environment
- **Language:** C99 / C++ (Bare-metal / Homebrew environment).
- **Toolchain:** `devkitPro` (specifically `devkitARM`) and `libnds`.
- **Target:** `.nds` binary format (compatible with TWiLight Menu++ on DSi/3DS).
- **Build System:** Must be reproducible. We will use a `Dockerfile` based on the official `devkitpro/devkitarm` image and a strict `Makefile`.

## 4. Core Dependencies (To be integrated statically)
1. **Bitcoin Cryptography:** `libsecp256k1` (Optimized for ARM, for elliptic curve signatures).
2. **QR Reading:** `quirc` (Lightweight C library to extract QR data from the camera feed).
3. **QR Generation:** `qrcodegen` (Project Nayuki's C library to render QRs on the top LCD).
4. **PSBT Parsing:** A lightweight BIP-174 (PSBT) parser suitable for embedded systems with limited RAM (4MB - 16MB). *When implementing this, strictly reference the parsing logic and data structures used in the official SeedSigner repository.*

## 5. UI / UX Flow
The Nintendo DS has two screens (Top: standard, Bottom: touchscreen).
- **Bottom Screen (Touch):** Used exclusively for user input. It must render a custom QWERTY keyboard and numeric pad to easily input a BIP-39 Passphrase (the 13th/25th word) using the stylus.
- **Top Screen:** Used for UI prompts, rendering the live camera feed (to scan external QRs), and rendering the final signed transaction QR code.

*Note: The sequence of UI screens, user prompts, and state management should mirror the original SeedSigner UX flow as closely as possible.*

## 6. Development Phases (Your tasks)
I want you to act as the lead embedded software engineer. Let's tackle this step by step. Do not write the whole app at once.

**Phase 1: Project Initialization & Toolchain**
- Generate a `Dockerfile` pulling `devkitpro/devkitarm`.
- Create a standard `Makefile` for a libnds project.
- Create a basic `src/main.c` that simply initializes the two screens, prints "NDS-Signer Init" on the top screen, and waits for the START button to exit.

**Phase 2: Camera & Screen Integration**
- Implement the `libnds` camera initialization (specifically for DSi).
- Render the live camera feed on the Top Screen.
- Create a basic touch-detection loop on the Bottom Screen.

Please acknowledge this architecture document and begin executing **Phase 1**. Create the directory structure, the Dockerfile, the Makefile, and the initial `main.c`. Let me know when it's ready to compile.