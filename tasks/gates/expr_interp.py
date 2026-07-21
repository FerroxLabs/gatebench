#!/usr/bin/env python3
import sys, importlib.util
def load(path):
    spec = importlib.util.spec_from_file_location("cand_ei", path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m
def checks(f):
    return [
        ("a=1+2 -> {a:3}", lambda: f("a = 1 + 2") == {"a": 3}),
        ("multi stmt uses prior binding", lambda: f("a = 2; b = a * 3") == {"a": 2, "b": 6}),
        ("chained env a=3;b=a;c=a*b", lambda: f("a=3; b=a; c=a*b") == {"a": 3, "b": 3, "c": 9}),
        ("reassignment a=1;a=a+1 -> a:2", lambda: f("a=1; a=a+1") == {"a": 2}),
        ("** right assoc 2**3**2 -> 512", lambda: f("x = 2**3**2") == {"x": 512}),
        ("unary lower than ** : -3**2 -> -9", lambda: f("v = -3**2") == {"v": -9}),
        ("unary after op 2*-3 -> -6", lambda: f("y = 2*-3") == {"y": -6}),
        ("double unary --2 -> 2", lambda: f("z = --2") == {"z": 2}),
        ("floor div 7//2 -> 3", lambda: f("q = 7 // 2") == {"q": 3}),
        ("mod 7%3 -> 1", lambda: f("m = 7 % 3") == {"m": 1}),
        ("precedence 1+2*3 -> 7", lambda: f("r = 1 + 2 * 3") == {"r": 7}),
        ("parens (1+2)*3 -> 9", lambda: f("r = (1+2)*3") == {"r": 9}),
        ("empty program -> {}", lambda: f("") == {}),
        ("only semicolons -> {}", lambda: f(";;") == {}),
        ("whitespace-only -> {}", lambda: f("   \n\t ") == {}),
        ("trailing semicolon a=1; -> {a:1}", lambda: f("a=1;") == {"a": 1}),
        ("newlines insignificant a\\n=\\n1+2", lambda: f("a\n=\n1\n+\n2") == {"a": 3}),
        ("bare expr binds nothing '1+2' -> {}", lambda: f("1+2") == {}),
        ("undefined var reference -> None", lambda: f("a = b") is None),
        ("bare undefined var -> None", lambda: f("a=1; b") is None),
        ("div by zero -> None", lambda: f("a = 1//0") is None),
        ("mod by zero -> None", lambda: f("a = 1%0") is None),
        ("assign to literal 1=2 -> None", lambda: f("1 = 2") is None),
        ("assign to expr a+b=3 -> None", lambda: f("a+b = 3") is None),
        ("trailing operator a=1+ -> None", lambda: f("a = 1+") is None),
        ("unbalanced paren a=(1+2 -> None", lambda: f("a = (1+2") is None),
        ("two literals a=1 2 -> None", lambda: f("a = 1 2") is None),
        ("empty parens a=() -> None", lambda: f("a = ()") is None),
        ("unknown char a=1$2 -> None", lambda: f("a = 1 $ 2") is None),
    ]
def main():
    try:
        m = load(sys.argv[1]); f = getattr(m, "run_program")
    except Exception as e:
        print(f"FAIL load/run_program missing: {e}"); print("gate: 0/29"); return
    passed = 0; cs = checks(f)
    for desc, fn in cs:
        try: ok = bool(fn())
        except Exception: ok = False
        if ok: passed += 1
        else: print(f"FAIL {desc}")
    print(f"gate: {passed}/{len(cs)}")
if __name__ == "__main__": main()
