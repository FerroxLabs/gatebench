#!/usr/bin/env python3
import sys, importlib.util
def load(path):
    spec = importlib.util.spec_from_file_location("cand2", path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m
def checks(f):
    return [
        ("1h30m == 5400", lambda: f("1h30m") == 5400),
        ("90m == 5400", lambda: f("90m") == 5400),
        ("1h2m3s == 3723", lambda: f("1h2m3s") == 3723),
        ("45s == 45", lambda: f("45s") == 45),
        ("0s == 0", lambda: f("0s") == 0),
        ("reject bare number 90", lambda: f("90") is None),
        ("reject out-of-order 30m1h", lambda: f("30m1h") is None),
        ("reject repeat 1h1h", lambda: f("1h1h") is None),
        ("reject inner space '1h 30m'", lambda: f("1h 30m") is None),
        ("reject unknown unit 5d", lambda: f("5d") is None),
        ("reject unit-no-number 'h'", lambda: f("h") is None),
        ("reject empty", lambda: f("") is None),
        ("reject trailing junk '1h30'", lambda: f("1h30") is None),
        ("reject negative '-1h'", lambda: f("-1h") is None),
    ]
def main():
    try:
        m = load(sys.argv[1]); f = getattr(m, "parse_duration")
    except Exception as e:
        print(f"FAIL load/parse_duration missing: {e}"); print("gate: 0/14"); return
    passed = 0; cs = checks(f)
    for desc, fn in cs:
        try: ok = bool(fn())
        except Exception: ok = False
        if ok: passed += 1
        else: print(f"FAIL {desc}")
    print(f"gate: {passed}/{len(cs)}")
if __name__ == "__main__": main()
