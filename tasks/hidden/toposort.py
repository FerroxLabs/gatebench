#!/usr/bin/env python3
# HIDDEN mutation gate — adversarial checks NEVER shown to the builder.
import sys, importlib.util
def load(path):
    spec = importlib.util.spec_from_file_location("hcand_ts", path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m
def checks(f):
    return [
        ("self-loop among valid nodes -> None", lambda: f({"a": ["b"], "b": [], "c": ["c"]}) is None),
        ("disjoint components deterministic",
         lambda: f({"a": ["b"], "b": [], "x": ["y"], "y": []}) == ["b", "a", "y", "x"]),
        ("multi-dotdot chain resolves order",
         lambda: f({"e": ["d"], "d": ["c"], "c": ["b"], "b": ["a"], "a": []}) == ["a", "b", "c", "d", "e"]),
        ("dep appears many times dedup", lambda: f({"a": ["b", "b", "b"], "b": []}) == ["b", "a"]),
        ("wide fan-in tie-break",
         lambda: f({"root": [], "a": ["root"], "c": ["root"], "b": ["root"]}) == ["root", "a", "b", "c"]),
        ("all absent-as-key deps", lambda: f({"top": ["m", "z", "a"]}) == ["a", "m", "z", "top"]),
        ("longer cycle -> None", lambda: f({"a": ["b"], "b": ["c"], "c": ["d"], "d": ["a"]}) is None),
        ("string sort multidigit '10' before '9'",
         lambda: f({"10": [], "9": [], "2": []}) == ["10", "2", "9"]),
        ("single node self only -> None", lambda: f({"only": ["only"]}) is None),
        ("returns permutation of all nodes",
         lambda: sorted(f({"p": ["q"], "q": ["r"], "r": []})) == ["p", "q", "r"]),
    ]
def main():
    try:
        m = load(sys.argv[1]); f = getattr(m, "toposort")
    except Exception as e:
        print(f"FAIL load: {e}"); print("hidden: 0/10"); return
    passed = 0; cs = checks(f)
    for desc, fn in cs:
        try: ok = bool(fn())
        except Exception: ok = False
        if ok: passed += 1
        else: print(f"HFAIL {desc}")
    print(f"hidden: {passed}/{len(cs)}")
if __name__ == "__main__": main()
