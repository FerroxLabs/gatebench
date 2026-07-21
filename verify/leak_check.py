#!/usr/bin/env python3
"""CI leak gate: scan every tracked file in the repo for private-infrastructure markers.

Patterns are assembled from fragments below so this file does not trip its own scan.
The secret-key-prefix pattern ("sk" followed by a hyphen) is matched with a word boundary,
so e.g. "task-specific" is not a hit but a real key prefix is. Everything else is a plain
substring match.

Exit status: 0 iff the repo is clean; nonzero (with per-hit report) otherwise.
Usage: python verify/leak_check.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules"}

# (label, compiled regex) — built from fragments so the patterns don't appear literally here.
PATTERNS = [
    ("sk" + "-key-prefix", re.compile(r"\b" + "sk" + "-")),
    ("keys" + ".env", re.compile(re.escape("keys" + ".env"))),
    ("flux" + "router", re.compile(re.escape("flux" + "router"), re.IGNORECASE)),
    ("dev/" + "anvil", re.compile(re.escape("dev/" + "anvil"))),
    ("dev/" + "flux", re.compile(re.escape("dev/" + "flux"))),
    ("systems" + ".py", re.compile(re.escape("systems" + ".py"))),
    ("/Use" + "rs/", re.compile(re.escape("/Use" + "rs/"))),
    ("Anvil" + "TestKey", re.compile(re.escape("Anvil" + "TestKey"))),
    ("x-" + "flux", re.compile(re.escape("x-" + "flux"), re.IGNORECASE)),
]


def main():
    hits = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in sorted(filenames):
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, ROOT)
            try:
                text = open(path, encoding="utf-8", errors="replace").read()
            except Exception as e:
                print(f"WARN cannot read {rel}: {e}")
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                for label, rx in PATTERNS:
                    if rx.search(line):
                        hits += 1
                        print(f"LEAK {rel}:{lineno} [{label}] {line.strip()[:120]}")
    if hits:
        print(f"\nFAIL: {hits} leak hit(s).")
        sys.exit(1)
    print("leak check: clean (no private-infrastructure markers found).")


if __name__ == "__main__":
    main()
