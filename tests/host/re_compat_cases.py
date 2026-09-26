# Regex cases for the MicroPython `re` compatibility module
# (mpy/frozen/compat/re.py). Patterns are the ones SeedSigner uses
# (grep -r "re\.(search|match|...)" in third_party/seedsigner/src).
I = 2  # re.IGNORECASE in both CPython and the compat module

ADDR = r'^((bc1|tb1|bcr|[123]|[mn])[a-zA-HJ-NP-Z0-9]{25,62})$'
ADDR2 = r'^((bc1q|tb1q|bcrt1q|bc1p|tb1p|bcrt1p|[123]|[mn])[a-zA-HJ-NP-Z0-9]{25,64})'
SPECTER = r'^p(\d+)of(\d+) ([A-Za-z0-9+\/=]+$)'

CASES = [
    ("^UR:CRYPTO-PSBT/", I, "ur:crypto-psbt/1-3/lpadax"),
    ("^UR:CRYPTO-PSBT/", I, "UR:CRYPTO-PSBT/abc"),
    ("^UR:CRYPTO-PSBT/", I, "xur:crypto-psbt/"),
    ("^UR:CRYPTO-OUTPUT/", I, "Ur:Crypto-Output/x"),
    ("^UR:CRYPTO-ACCOUNT/", I, "ur:crypto-account/x"),
    ("^UR:BYTES/", I, "ur:bytes/hdcx"),
    ("^UR:BYTES/", 0, "ur:bytes/hdcx"),
    (SPECTER, I, "p1of3 cHNidP8BAHICAAAAAQDo5ey+"),
    (SPECTER, I, "P12OF30 abc=="),
    (SPECTER, I, "p1of3 not base64!"),
    (r'^p(\d+)of(\d+) ', I, "p2of2 {\"label\""),
    (r'^p(\d+)of(\d+) (.+$)', I, "p2of5 hello world"),
    (r"^B\$[2HZ]P[0-9A-Z]{4}", 0, "B$ZP0100FMUE4K"),
    (r"^B\$[2HZ]P[0-9A-Z]{4}", 0, "B$ZP01"),
    (r"^B\$[2HZ]P[0-9A-Z]{4}", 0, "B$XP0100"),
    (r'^\{\"label\".*\"descriptor\"\:.*', I, '{"label":"x","descriptor":"wsh(...)"}'),
    (r'^\{\"label\".*\"descriptor\"\:.*', I, '{"LABEL":"x","Descriptor":"y"}'),
    (r'\d{48,96}', 0, "0801150603870631040718570676186811251362077313540"),
    (r'\d{48,96}', 0, "08011506038706310407185706761868112513620773135"),
    (r'\d{48,96}', 0, "x" + "1" * 120 + "y"),
    (r'^bitcoin\:.*', I, "BITCOIN:bc1q8wfyqsah7pfehz3yz6j8wz9r0ha5v3h4wcsk4p"),
    (ADDR, I, "bc1q8wfyqsah7pfehz3yz6j8wz9r0ha5v3h4wcsk4p"),
    (ADDR, I, "BC1Q8WFYQSAH7PFEHZ3YZ6J8WZ9R0HA5V3H4WCSK4P"),
    (ADDR, I, "tb1que40al7rsw88ru9z0vr78vqwme4w3ctqj694kx"),
    (ADDR, I, "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"),
    (ADDR, I, "mipcBbFg9gMiCh81Kj8tqqdgoZub1ZJRfn"),
    (ADDR, I, "bc1qshort"),
    (ADDR, I, "bc1q" + "a" * 70),
    (ADDR, I, "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2 trailing"),
    (ADDR2, I, "tb1qrgkyutwsjmp5vr3fxeuecll8qpvgwvnth2wa5k?amount=1"),
    (ADDR2, I, "2N1Agr9voB5g4BhaTihLCuGFTFbbPBHVt7T"),
    (r'(\d+)\D*(\d+)', 0, "Pages 12 of 30"),
    (r'[^,\s]+', 0, "a, b ,c"),
]
