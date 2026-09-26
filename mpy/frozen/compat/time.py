# NDS-Signer - `time` stub. The signer has no use for wall-clock time (the
# ARM7 core does not even start the RTC); only log timestamps need it.


def time():
    return 0


def localtime(t=None):
    return (2000, 1, 1, 0, 0, 0, 5, 1)


def strftime(fmt, t=None):
    return ""
