# Installing NDS-Signer

*[Leer en español](es/instalar.md)*

## Which consoles work

| Console | Works? | Notes |
| :--- | :---: | :--- |
| Nintendo DS (2004) | ❌ No | 4 MB of RAM: NDS-Signer needs over 8 (6 MB of Python heap, 2 MB of code). Telephone tones would replace its missing camera, not its memory. |
| Nintendo DS Lite | ❌ No | The same: 4 MB of RAM. |
| Nintendo DSi | ✅ Yes | Same hardware as the DSi XL. |
| Nintendo DSi XL (DSi LL in Japan) | ✅ Yes | The console NDS-Signer is tested on. |
| Nintendo 3DS, 3DS XL, 2DS, New 3DS, New 3DS XL, New 2DS XL | ❓ Untested | They run DSi software, but the camera, the lid and the power button have not been tried with NDS-Signer. Reports welcome ([help wanted](help-wanted.md)). |
| Emulators (melonDS…) | ⚠️ Development only | A computer is not air-gapped: never use a real seed in an emulator. |

Any region. A working camera scans QR codes; without one (or with a broken
one), PSBTs and seeds can come in as [telephone tones](../README.md#telephone-tones-experimental)
(experimental), by cable or through the air, so a DSi can still sign.

## What you need

- A DSi or DSi XL and its charger.
- An SD card (the DSi guide below explains which sizes and format work).
- A computer to prepare the SD card.

## 1 · Prepare the console (once)

A DSi only runs Nintendo's software until a homebrew launcher is installed.
Follow **[dsi.cfw.guide](https://dsi.cfw.guide)**, the community guide, from
*Get Started*: it installs **Unlaunch**, which lets the DSi start programs
from the SD card. Do the NAND backup it offers: it is your way back if
anything goes wrong.

Optional: **[TWiLight Menu++](https://wiki.ds-homebrew.com/twilightmenu/installing-dsi)**,
a menu to browse and launch the programs on the SD card.

Download these tools only from the guides' links.

## 2 · Get NDS-Signer

1. Download `nds-signer.nds` and `SHA256.txt` from the
   [releases](https://github.com/ndssigner/nds-signer/releases) on GitHub. Official releases are published
   only there.
2. Check the file:
   - macOS / Linux: `shasum -a 256 nds-signer.nds`
   - Windows: `certutil -hashfile nds-signer.nds SHA256`

   The result must be the hash in `SHA256.txt`. If it is not, do not use the
   file. For the strongest check, [build it yourself](../README.md#build): the
   same version gives the same hash.
3. Copy `nds-signer.nds` to the SD card, for example to its root folder.

## 3 · Start it

- **From Unlaunch:** hold **A + B** while switching the DSi on; Unlaunch's
  menu lists the files on the SD card: choose `nds-signer.nds`.
- **From TWiLight Menu++:** open it like any other program. If the camera
  does not work when launched this way, start NDS-Signer from Unlaunch.

The Home screen shows **NDS-Signer** and its version. The wireless light
switches off as it starts.

## 4 · First steps

1. *Settings → Advanced → Bitcoin network*: try **Testnet/Signet** first.
2. Load a seed (*Seeds*), or make a test one (*Tools → New seed*).
3. Create a watch-only wallet on your computer by exporting the xpub
   (*Seeds → your seed → Export Xpub*) and scanning it with Sparrow.
4. Sign a test transaction: build it in Sparrow, *Scan* it with the DSi,
   review, approve, and scan the signed QR code back into Sparrow.

Which wallets work: see the [README](../README.md#compatible-wallets).

## Good practice

- **Keep the SD card for NDS-Signer:** only Unlaunch/TWiLight Menu++ and
  NDS-Signer, all from official sources. Anything that runs before
  NDS-Signer could tamper with it.
- **Nothing about your seed goes on the SD card**, ever: no photos, no
  notes. NDS-Signer never writes to it.
- **Close the lid when you are done:** NDS-Signer wipes its memory and
  switches the console off.
- **Updating:** replace `nds-signer.nds` with the new version, after checking
  its hash.
