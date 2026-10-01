# Why NDS-Signer exists

*[Leer en español](es/por-que.md) (original text; this is a translation)*

## The drawbacks of the "classic" SeedSigner

Although I don't own one, I have always thought *SeedSigner* is a fantastic
tool for Bitcoin self-custody. The main drawback I see is having to build
one yourself or buy one already assembled.

I think two rather sensitive issues affect
*SeedSigner*'s philosophy:

1) **The usual hardware is very recognisable.** Even though it is a DIY
   solution, everyone tends towards the same Pi Zero + camera + buttons
   setup, often with the same case. In most cases it is as recognisable as
   a *Trezor* or a *Coldcard*. This can seriously undermine plausible
   deniability: whoever owns a *SeedSigner* probably owns some bitcoin
   (and is exposed to the "$5 wrench attack").

2) **The hardware has a single purpose.** If you have a Pi Zero with its
   camera and buttons, what else will you use it for? It would be another
   matter if the Pi Zero lived in another project (say, a mini console with
   emulators) and you only added the components and the microSD card that
   turn it into a SeedSigner when needed, but that is not going to happen.

It is also amusing to see how many hardware wallet makers try to disguise
their wallets as other devices: calculators (*Coldcard MK*), BlackBerrys
(*Coldcard Q*), classic phones, smartphones, e-readers… But with ever more
capable AI models, the operator of an X-ray scanner no longer needs to know
what on earth a device is: the scanner itself will tell them, and flag it.

## Plausible deniability by borrowing vintage devices

The real motivation for porting *SeedSigner* to the Nintendo DS is to reuse
a device that genuinely serves another purpose (playing games), and that is
reasonably safe from remote attacks (something today's smartphones do not
offer), to host a signer (or even a *wallet*, for the bold).

My original idea was to build something for the Game Boy: open-source
hardware with its own digital camera that would use the console's interface
to do what *SeedSigner* does… But besides being complicated, it would bring
supply-chain risks: tampering with the firmware or the hardware (not only
at the chip or silicon level; they might even add *extras*), or leaks of
the postal addresses the devices are shipped to (it has already happened to
several manufacturers, such as Trezor).

That is why I think the ideal is to use old consoles that have cameras, so
the software can be used discreetly. Unless it looks badly out of place, a
console raises no suspicion. Being software, you can download it over Tor,
check its SHA-256 and copy the ROM to the SD card without anyone linking it
to you. And there is a large second-hand market for these consoles, at
around 50 USD: much cheaper than building a *SeedSigner*.

So I encourage other developers to follow this philosophy: find existing
hardware that can run *SeedSigner*'s software without drawing attention:
game consoles (the PS Vita would be another candidate), photo and video
cameras, scanners, netbooks, PDAs, etc.

Along these lines, having *SeedSigner* on old (offline) devices and the
wallet on the latest devices is a very interesting combination. However,
since QR codes need a camera on the receiving side, many opportunities are
lost. Transferring data by audio, infrared, a serial port… should be
considered. Imagine a *SeedSigner* running on an unmodified *HP 48*, a
*Game Boy* or a *Commodore 64*!

## The nature of the project, maintainers and disclaimer

This project was made entirely with **love and *vibe coding***, with the
help of **Claude Opus 5.5**. Anyone who wants to contribute to it, or even
maintain it, is welcome to.

I am personally not very familiar with open-source development and don't
know how collaboration usually works. Nor do I have the time or the will to
take this beyond a weekend project: I am not Linus Torvalds.

That said, **I take no responsibility** for the good or bad use anyone may
make of this software, or for any loss of bitcoin a user may suffer. That
is why I have made sure the core of this system is based entirely on
*SeedSigner*'s original code.
