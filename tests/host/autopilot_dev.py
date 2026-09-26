# Autopilot for checking the developer build in the emulator
# (make DEVBUILD=1 AUTOTEST=1 AUTOPILOT=dev MPY_APP=1): open diagnostics with
# SELECT, run the benchmark, then show the report as a QR code.
KEY_SELECT = 1 << 2
EVENTS = [("log", "start"), ("wait", 30), ("key", KEY_SELECT), ("wait", 30),
          ("tap_label", "Benchmark"), ("wait", 60), ("tap_label", "Show as QR"), ("log", "done")]
