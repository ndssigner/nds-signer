# Lists every (module, name) that upstream non-GUI SeedSigner code imports from
# seedsigner.gui / seedsigner.hardware (replaced by NDS-Signer's overlay), as
# JSON for gui_imports_check.py. Runs on CPython.
import ast
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1]) / "seedsigner"
pairs = set()
for path in [root / "controller.py"] + [p for d in ("views", "models", "helpers")
                                        for p in (root / d).rglob("*.py")]:
    for node in ast.walk(ast.parse(path.read_text())):
        if (isinstance(node, ast.ImportFrom) and node.module
                and node.module.startswith(("seedsigner.gui", "seedsigner.hardware"))):
            for alias in node.names:
                pairs.add((node.module, alias.name))
json.dump(sorted(pairs), sys.stdout)
