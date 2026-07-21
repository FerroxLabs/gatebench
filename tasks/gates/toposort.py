#!/usr/bin/env python3
import sys, importlib.util, importlib.machinery
def load(path):
    # Explicit SourceFileLoader: the native gate-first executor writes candidates as
    # artifact-N.txt; spec_from_file_location alone yields loader=None for non-.py paths.
    loader = importlib.machinery.SourceFileLoader("cand_ts", path)
    spec = importlib.util.spec_from_file_location("cand_ts", path, loader=loader)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m
def checks(f):
    return [
        ("empty {} -> []", lambda: f({}) == []),
        ("single {a:[]} -> [a]", lambda: f({"a": []}) == ["a"]),
        ("chain a->b->c -> [c,b,a]", lambda: f({"a": ["b"], "b": ["c"], "c": []}) == ["c", "b", "a"]),
        ("tie-break roots sorted", lambda: f({"z": [], "a": [], "m": []}) == ["a", "m", "z"]),
        ("absent-as-key node included first", lambda: f({"a": ["b"]}) == ["b", "a"]),
        ("diamond deterministic",
         lambda: f({"d": ["b", "c"], "b": ["a"], "c": ["a"], "a": []}) == ["a", "b", "c", "d"]),
        ("duplicate dep dedup", lambda: f({"a": ["b", "b"], "b": []}) == ["b", "a"]),
        ("self-loop -> None", lambda: f({"a": ["a"]}) is None),
        ("two-cycle -> None", lambda: f({"a": ["b"], "b": ["a"]}) is None),
        ("partial cycle -> None", lambda: f({"a": ["b"], "b": ["a"], "c": []}) is None),
        ("three-cycle -> None", lambda: f({"a": ["b"], "b": ["c"], "c": ["a"]}) is None),
        ("layered app/lib/util", lambda: f({"app": ["lib", "util"], "lib": ["util"], "util": []}) == ["util", "lib", "app"]),
        ("shared dep freed tie-break", lambda: f({"x": ["a"], "y": ["a"], "a": []}) == ["a", "x", "y"]),
        ("multi-root then join", lambda: f({"b": [], "a": [], "c": ["a", "b"]}) == ["a", "b", "c"]),
        ("absent chain a->b->r", lambda: f({"p": ["q"], "q": ["r"]}) == ["r", "q", "p"]),
        ("string order not numeric ('10'<'2')", lambda: f({"10": [], "2": []}) == ["10", "2"]),
        ("all nodes present (count)",
         lambda: sorted(f({"d": ["b", "c"], "b": ["a"], "c": ["a"], "a": []})) == ["a", "b", "c", "d"]),
        ("acyclic returns list not None", lambda: isinstance(f({"a": []}), list)),
    ]
def main():
    try:
        m = load(sys.argv[1]); f = getattr(m, "toposort")
    except Exception as e:
        print(f"FAIL load/toposort missing: {e}"); print("gate: 0/18"); return
    passed = 0; cs = checks(f)
    for desc, fn in cs:
        try: ok = bool(fn())
        except Exception: ok = False
        if ok: passed += 1
        else: print(f"FAIL {desc}")
    print(f"gate: {passed}/{len(cs)}")
if __name__ == "__main__": main()
