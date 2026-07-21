#!/usr/bin/env python3
# HIDDEN mutation gate — adversarial checks NEVER shown to the builder.
import sys, importlib.util
def load(path):
    spec = importlib.util.spec_from_file_location("hcand_sv", path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m
def raises(fn):
    try: fn(); return False
    except ValueError: return True
    except Exception: return False
def checks(iv, cmp):
    return [
        ("valid 10.20.30", lambda: iv("10.20.30") is True),
        ("valid long prerelease 1.0.0-a.1.2.3", lambda: iv("1.0.0-a.1.2.3") is True),
        ("valid alnum starting digit 1.0.0-0A", lambda: iv("1.0.0-0A") is True),
        ("valid build 1.0.0+build.1", lambda: iv("1.0.0+build.1") is True),
        ("invalid leading zero minor 1.01.0", lambda: iv("1.01.0") is False),
        ("invalid leading zero patch 1.0.01", lambda: iv("1.0.01") is False),
        ("major beats prerelease 2.0.0-alpha > 1.9.9", lambda: cmp("2.0.0-alpha", "1.9.9") == 1),
        ("equal full prerelease", lambda: cmp("1.0.0-alpha.beta", "1.0.0-alpha.beta") == 0),
        ("numeric pre chain 1.2.3 < 1.2.4", lambda: cmp("1.0.0-1.2.3", "1.0.0-1.2.4") == -1),
        ("build ignored with prerelease", lambda: cmp("1.0.0-a+x", "1.0.0-a+y") == 0),
        ("patch precedence", lambda: cmp("1.0.1", "1.0.0") == 1),
        ("alnum lexical not numeric: alpha10 < alpha9", lambda: cmp("1.0.0-alpha10", "1.0.0-alpha9") == -1),
        ("both invalid raises", lambda: raises(lambda: cmp("x", "y"))),
        ("second invalid raises", lambda: raises(lambda: cmp("1.0.0", "1.0"))),
    ]
def main():
    try:
        m = load(sys.argv[1]); iv = getattr(m, "is_valid"); cmp = getattr(m, "compare")
    except Exception as e:
        print(f"FAIL load: {e}"); print("hidden: 0/14"); return
    passed = 0; cs = checks(iv, cmp)
    for desc, fn in cs:
        try: ok = bool(fn())
        except Exception: ok = False
        if ok: passed += 1
        else: print(f"HFAIL {desc}")
    print(f"hidden: {passed}/{len(cs)}")
if __name__ == "__main__": main()
