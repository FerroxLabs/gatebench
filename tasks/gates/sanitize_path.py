#!/usr/bin/env python3
# Independent acceptance gate for sanitize_path. Contract: python3 gate.py <candidate.py>
# Prints one `FAIL <desc>` per failing check and a final `gate: <passed>/<total>` line.
import sys, importlib.util, unicodedata

def load(path):
    spec = importlib.util.spec_from_file_location("cand", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

B = "/srv/data"
# (description, callable -> bool expected-true)
def checks(f):
    return [
        ("join safe relative stays inside base",
         lambda: (r := f(B, "a/b.txt")) is not None and r.startswith(B) and r.endswith("a/b.txt")),
        ("nested safe relative accepted",
         lambda: (r := f(B, "x/y/z.txt")) is not None and r.startswith(B)),
        ("reject parent traversal ../etc/passwd",
         lambda: f(B, "../etc/passwd") is None),
        ("reject absolute /etc/passwd",
         lambda: f(B, "/etc/passwd") is None),
        ("reject empty",
         lambda: f(B, "") is None),
        ("reject bare ..",
         lambda: f(B, "..") is None),
        ("reject mid traversal a/../../etc",
         lambda: f(B, "a/../../etc") is None),
        ("reject NFKC homoglyph fullwidth-dot traversal",
         lambda: f(B, "．．/etc") is None),
        ("reject NUL byte",
         lambda: f(B, "a\x00b") is None),
    ]

def main():
    try:
        m = load(sys.argv[1])
        f = getattr(m, "sanitize_path")
    except Exception as e:
        print(f"FAIL module load / sanitize_path missing: {e}")
        print("gate: 0/9")
        return
    passed = 0
    cs = checks(f)
    for desc, fn in cs:
        try:
            ok = bool(fn())
        except Exception:
            ok = False
        if ok:
            passed += 1
        else:
            print(f"FAIL {desc}")
    print(f"gate: {passed}/{len(cs)}")

if __name__ == "__main__":
    main()
