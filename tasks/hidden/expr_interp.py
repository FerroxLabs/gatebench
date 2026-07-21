#!/usr/bin/env python3
# HIDDEN mutation gate — adversarial checks NEVER shown to the builder.
import sys, importlib.util
def load(path):
    spec = importlib.util.spec_from_file_location("hcand_ei", path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m
def checks(f):
    return [
        ("mixed precedence 2+3*4-5//2 -> 12", lambda: f("r = 2 + 3 * 4 - 5 // 2") == {"r": 12}),
        ("nested parens ((1)) -> 1", lambda: f("r = ((1))") == {"r": 1}),
        ("(2**2)**3 -> 64", lambda: f("r = (2**2)**3") == {"r": 64}),
        ("unary over parens -(3+4) -> -7", lambda: f("r = -(3+4)") == {"r": -7}),
        ("mod then add 10%3+1 -> 2", lambda: f("r = 10 % 3 + 1") == {"r": 2}),
        ("reassign uses old value", lambda: f("a=5; a=a*a; a=a-1") == {"a": 24}),
        ("deep nesting 2*(3+4*(5-1)) -> 38", lambda: f("x = 2*(3+4*(5-1))") == {"x": 38}),
        ("double-equals is error", lambda: f("a == 1") is None),
        ("leading equals is error", lambda: f("= 1") is None),
        ("two names before eq is error", lambda: f("a b = 1") is None),
        ("undefined var mid-program", lambda: f("a=1; c=a+z") is None),
        ("empty statement between semicolons", lambda: f("a=1;; b=2") == {"a": 1, "b": 2}),
        ("power over unary rhs 2**3 -> 8, keep int", lambda: f("p = 2**3") == {"p": 8}),
        ("left assoc subtraction 10-3-2 -> 5", lambda: f("q = 10-3-2") == {"q": 5}),
        ("left assoc floordiv 100//5//2 -> 10", lambda: f("q = 100//5//2") == {"q": 10}),
    ]
def main():
    try:
        m = load(sys.argv[1]); f = getattr(m, "run_program")
    except Exception as e:
        print(f"FAIL load: {e}"); print("hidden: 0/15"); return
    passed = 0; cs = checks(f)
    for desc, fn in cs:
        try: ok = bool(fn())
        except Exception: ok = False
        if ok: passed += 1
        else: print(f"HFAIL {desc}")
    print(f"hidden: {passed}/{len(cs)}")
if __name__ == "__main__": main()
