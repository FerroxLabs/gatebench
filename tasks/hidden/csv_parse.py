#!/usr/bin/env python3
# HIDDEN mutation gate — adversarial checks NEVER shown to the builder.
import sys, importlib.util
def load(path):
    spec = importlib.util.spec_from_file_location("hcand_csv", path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m
def checks(f):
    return [
        ("CRLF trailing no extra record", lambda: f("a\r\n") == [["a"]]),
        ("quoted empty then data", lambda: f('"",x') == [["", "x"]]),
        ("bare quote mid unquoted field literal", lambda: f('a"b') == [['a"b']]),
        ("trailing comma then LF", lambda: f("a,\n") == [["a", ""]]),
        ("commas and newline grid", lambda: f(",\n,") == [["", ""], ["", ""]]),
        ("nested escaped quotes", lambda: f('"he said ""hi"""') == [['he said "hi"']]),
        ("windows two-row file", lambda: f("name,age\r\nbob,30\r\n") == [["name", "age"], ["bob", "30"]]),
        ("quoted empties around", lambda: f('"a","","c"') == [["a", "", "c"]]),
        ("quote holds separator then real sep", lambda: f('"a\nb"\nc') == [["a\nb"], ["c"]]),
        ("many empty fields", lambda: f(",,,") == [["", "", "", ""]]),
        ("single char", lambda: f("x") == [["x"]]),
        ("quoted with trailing text lenient", lambda: f('"a"bc,d') == [["abc", "d"]]),
    ]
def main():
    try:
        m = load(sys.argv[1]); f = getattr(m, "parse_csv")
    except Exception as e:
        print(f"FAIL load: {e}"); print("hidden: 0/12"); return
    passed = 0; cs = checks(f)
    for desc, fn in cs:
        try: ok = bool(fn())
        except Exception: ok = False
        if ok: passed += 1
        else: print(f"HFAIL {desc}")
    print(f"hidden: {passed}/{len(cs)}")
if __name__ == "__main__": main()
