# Prints one line per regex case. Run under CPython (reference) and under
# MicroPython with mpy/frozen/compat on the module path; outputs must match.
import re
from re_compat_cases import CASES

for pattern, flags, text in CASES:
    try:
        if pattern == r'[^,\s]+':
            print(pattern, "|", re.findall(pattern, text, flags))
            continue
        m = re.search(pattern, text, flags)
        if m is None:
            print(pattern, "|", None)
        else:
            try:
                groups = m.groups()
            except AttributeError:
                groups = ()
            print(pattern, "|", m.group(0), "|", groups)
    except Exception as e:
        print(pattern, "|", "ERROR", type(e).__name__)
