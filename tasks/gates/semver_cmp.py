#!/usr/bin/env python3
import sys, importlib.util
def load(path):
    spec = importlib.util.spec_from_file_location("cand_sv", path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m
def raises(fn):
    try:
        fn(); return False
    except ValueError:
        return True
    except Exception:
        return False
def checks(iv, cmp):
    return [
        ("valid 1.0.0", lambda: iv("1.0.0") is True),
        ("valid 0.0.0", lambda: iv("0.0.0") is True),
        ("valid 1.2.3-alpha", lambda: iv("1.2.3-alpha") is True),
        ("valid 1.2.3-alpha.1", lambda: iv("1.2.3-alpha.1") is True),
        ("valid 1.2.3-0.3.7 (numeric ids)", lambda: iv("1.2.3-0.3.7") is True),
        ("valid hyphen ids 1.2.3-x-y-z.-", lambda: iv("1.2.3-x-y-z.-") is True),
        ("valid build leading zeros 1.0.0-a+001", lambda: iv("1.0.0-alpha+001") is True),
        ("valid build only 1.0.0+20130313144700", lambda: iv("1.0.0+20130313144700") is True),
        ("valid 1.0.0-beta+exp.sha.5114f85", lambda: iv("1.0.0-beta+exp.sha.5114f85") is True),
        ("invalid leading zero major 01.0.0", lambda: iv("01.0.0") is False),
        ("invalid two-part 1.0", lambda: iv("1.0") is False),
        ("invalid trailing dash 1.0.0-", lambda: iv("1.0.0-") is False),
        ("invalid leading-zero prerelease 1.0.0-01", lambda: iv("1.0.0-01") is False),
        ("invalid empty build 1.0.0+", lambda: iv("1.0.0+") is False),
        ("invalid empty pre id 1.0.0-a..b", lambda: iv("1.0.0-a..b") is False),
        ("invalid four parts 1.2.3.4", lambda: iv("1.2.3.4") is False),
        ("invalid underscore 1.0.0-alpha_beta", lambda: iv("1.0.0-alpha_beta") is False),
        ("invalid v-prefix v1.0.0", lambda: iv("v1.0.0") is False),
        ("cmp 1.0.0 < 2.0.0", lambda: cmp("1.0.0", "2.0.0") == -1),
        ("cmp 2.0.0 > 1.0.0", lambda: cmp("2.0.0", "1.0.0") == 1),
        ("cmp equal", lambda: cmp("1.0.0", "1.0.0") == 0),
        ("cmp minor 1.1.0 > 1.0.9", lambda: cmp("1.1.0", "1.0.9") == 1),
        ("prerelease < release", lambda: cmp("1.0.0-alpha", "1.0.0") == -1),
        ("more pre fields higher: alpha < alpha.1", lambda: cmp("1.0.0-alpha", "1.0.0-alpha.1") == -1),
        ("numeric < alnum: alpha.1 < alpha.beta", lambda: cmp("1.0.0-alpha.1", "1.0.0-alpha.beta") == -1),
        ("alpha.beta < beta", lambda: cmp("1.0.0-alpha.beta", "1.0.0-beta") == -1),
        ("beta < beta.2", lambda: cmp("1.0.0-beta", "1.0.0-beta.2") == -1),
        ("numeric compare beta.2 < beta.11", lambda: cmp("1.0.0-beta.2", "1.0.0-beta.11") == -1),
        ("rc.1 < release", lambda: cmp("1.0.0-rc.1", "1.0.0") == -1),
        ("build ignored +a == +b", lambda: cmp("1.0.0+a", "1.0.0+b") == 0),
        ("build ignored +build == none", lambda: cmp("1.0.0+build", "1.0.0") == 0),
        ("invalid input raises ValueError", lambda: raises(lambda: cmp("bad", "1.0.0"))),
    ]
def main():
    try:
        m = load(sys.argv[1]); iv = getattr(m, "is_valid"); cmp = getattr(m, "compare")
    except Exception as e:
        print(f"FAIL load/functions missing: {e}"); print("gate: 0/32"); return
    passed = 0; cs = checks(iv, cmp)
    for desc, fn in cs:
        try: ok = bool(fn())
        except Exception: ok = False
        if ok: passed += 1
        else: print(f"FAIL {desc}")
    print(f"gate: {passed}/{len(cs)}")
if __name__ == "__main__": main()
