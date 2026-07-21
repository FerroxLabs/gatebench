#!/usr/bin/env python3
import sys, importlib.util
def load(path):
    spec = importlib.util.spec_from_file_location("cand3", path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m
def checks(f):
    return [
        ("1+2*3 == 7", lambda: f("1+2*3") == 7),
        ("(1+2)*3 == 9", lambda: f("(1+2)*3") == 9),
        ("2**3**2 == 512 (right assoc)", lambda: f("2**3**2") == 512),
        ("7//2 == 3", lambda: f("7//2") == 3),
        ("7%3 == 1", lambda: f("7%3") == 1),
        ("-3+2 == -1 (unary)", lambda: f("-3+2") == -1),
        ("2*-3 == -6 (unary after op)", lambda: f("2*-3") == -6),
        ("spaces insignificant '((2+3)*4-1)//3' == 6", lambda: f("((2+3)*4-1)//3") == 6),
        ("spaces ' 1 + 2 * 3 ' == 7", lambda: f(" 1 + 2 * 3 ") == 7),
        ("reject div by zero 8//0", lambda: f("8//0") is None),
        ("reject mod by zero 8%0", lambda: f("8%0") is None),
        ("reject empty", lambda: f("") is None),
        ("reject trailing op '1+'", lambda: f("1+") is None),
        ("reject unbalanced '(1+2'", lambda: f("(1+2") is None),
        ("reject extra close '2+3)'", lambda: f("2+3)") is None),
        ("reject letters 'abc'", lambda: f("abc") is None),
        ("reject single slash '1/2'", lambda: f("1/2") is None),
        ("reject empty parens '()'", lambda: f("()") is None),
    ]
def main():
    try:
        m = load(sys.argv[1]); f = getattr(m, "safe_eval")
    except Exception as e:
        print(f"FAIL load/safe_eval missing: {e}"); print("gate: 0/18"); return
    passed = 0; cs = checks(f)
    for desc, fn in cs:
        try: ok = bool(fn())
        except Exception: ok = False
        if ok: passed += 1
        else: print(f"FAIL {desc}")
    print(f"gate: {passed}/{len(cs)}")
if __name__ == "__main__": main()
