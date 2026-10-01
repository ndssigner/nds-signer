# Security

NDS-Signer handles Bitcoin seeds. If you find a vulnerability, please report
it privately: use GitHub's **"Report a vulnerability"** button (Security tab
of this repository) rather than a public issue.

Useful to include: what an attacker can do, the steps to reproduce it, and
the NDS-Signer version (shown on the Home screen).

## Scope

- **NDS-Signer's own code:** the DSi layer (`arm7/`, `arm9/`, `mpy/`),
  screens, drivers, entropy tools, build.
- **SeedSigner and embit:** NDS-Signer runs them unmodified. A problem in
  PSBT verification, seed handling or signing that also affects SeedSigner
  should be reported to [SeedSigner](https://github.com/SeedSigner/seedsigner/security)
  or [embit](https://github.com/diybitcoinhardware/embit); please tell us
  too, so we can update the pinned versions.

## Known limits (not vulnerabilities)

- NDS-Signer trusts the console's boot chain (Unlaunch, TWiLight Menu++, the
  SD card's contents) that runs before it.
- Physical attacks on the console (modified hardware, memory read right
  after power-off) are out of scope.
- The project is an alpha and has not been audited.
