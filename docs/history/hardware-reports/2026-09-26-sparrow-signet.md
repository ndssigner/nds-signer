# First real transaction: Sparrow + Signet (2026-09-26, build dsi-test-2)

Setup: Sparrow 2.5.5 (Homebrew cask) on the Mac, Signet, public server; a
watch-only wallet from the test seed's account xpub (fingerprint 8b218e81,
m/84'/1'/0'); coins from a Signet faucet. Signing on the real DSi XL.
Guide: docs/es/guia-sparrow-signet.md.

| Step | Result |
| :--- | :--- |
| Sparrow shows the unsigned PSBT as an animated UR QR (low density chosen) | - |
| DSi XL scans the whole animation (held by hand) | **OK, ~29 s** |
| Review on the DSi (with change output) and approval | OK |
| Sparrow scans the DSi's signed animated QR with the Mac webcam | **OK, first try** |
| Broadcast | OK |

Transaction `33260b23240e63b452001c806a87e9fb86ac3f85d3198ec4cc7194c55cc338ac`
(Signet; mempool.space/signet): 1 input of 186,339 sats from
`tb1qw2as76rh...` (m/84'/1'/0'/0/0); outputs 10,000 sats to `tb1qg3lau83h...`
and 176,198 sats of change to `tb1qrgkyutws...`; fee 141 sats (140 vB).

Follow-ups:
- Scanning an animated QR takes ~29 s at low density: worth optimizing
  (decode frame rate, hardware scaling of the viewfinder) and testing high
  density.
- Users need the xpub export on the device (it was computed on the host for
  this test; the upstream Export Xpub screens still use generic stand-ins).
