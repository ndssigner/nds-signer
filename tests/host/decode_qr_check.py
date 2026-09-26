# Differential test for SeedSigner's DecodeQR: prints the decoder state for
# a set of QR payloads (single and animated UR). Output must be identical on
# CPython (upstream sources) and MicroPython (frozen, transformed sources).
import hashlib
import sys
from binascii import hexlify

from seedsigner.models.decode_qr import DecodeQR

VECTORS = sys.argv[1] if len(sys.argv) > 1 else "../vectors"


def read(name):
    try:
        import test_vectors  # frozen into the spike ROM (no filesystem on the DSi)
        return test_vectors.DATA[name].strip()
    except ImportError:
        with open(VECTORS + "/" + name) as f:
            return f.read().strip()


def report(label, parts):
    d = DecodeQR()
    status = None
    used = 0
    for part in parts:
        status = d.add_data(part)
        used += 1
        if d.is_complete:
            break
    line = [label, "status=%d" % int(status), "type=%s" % d.qr_type, "complete=%s" % d.is_complete,
            "parts=%d" % used]
    if d.is_complete and d.is_psbt:
        raw = d.get_psbt().serialize()
        line.append("psbt_sha256=%s" % hexlify(hashlib.sha256(raw).digest()).decode()[:16])
    if d.is_complete and d.is_address:
        line.append("address=%s type=%s" % (d.get_address(), d.get_address_type()))
    if d.is_complete and d.is_seed:
        line.append("words=%s" % " ".join(d.get_seed_phrase() or []))
    print(" ".join(line))


report("psbt-base64", [read("psbt_base64_singlesig.txt")])
report("psbt-ur-1in", read("psbt_base64_singlesig.ur.txt").split("\n"))
report("psbt-ur-10in", read("psbt_base64_10in.ur.txt").split("\n"))
report("address", [read("address_testnet.txt")])
report("address-uri", ["bitcoin:" + read("address_testnet.txt") + "?amount=0.001"])
report("seedqr", [read("seedqr_12words.txt")])
report("plain", [read("plain_text.txt")])
