#!/usr/bin/env python3
import sys, importlib.util
def load(path):
    spec = importlib.util.spec_from_file_location("cand_csv", path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m
def checks(f):
    return [
        ("simple 'a,b,c'", lambda: f("a,b,c") == [["a", "b", "c"]]),
        ("empty input -> []", lambda: f("") == []),
        ("two records LF", lambda: f("a,b\nc,d") == [["a", "b"], ["c", "d"]]),
        ("two records CRLF", lambda: f("a,b\r\nc,d") == [["a", "b"], ["c", "d"]]),
        ("trailing LF no extra record", lambda: f("a,b\n") == [["a", "b"]]),
        ("trailing CRLF no extra record", lambda: f("a,b\r\n") == [["a", "b"]]),
        ("trailing comma -> empty field", lambda: f("a,") == [["a", ""]]),
        ("leading comma -> empty field", lambda: f(",a") == [["", "a"]]),
        ("blank middle line -> ['']", lambda: f("a\n\nb") == [["a"], [""], ["b"]]),
        ("quoted field verbatim", lambda: f('"a"') == [["a"]]),
        ("quoted comma inside", lambda: f('"a,b",c') == [["a,b", "c"]]),
        ("quoted newline inside", lambda: f('"a\nb",c') == [["a\nb", "c"]]),
        ("quoted CRLF inside stays", lambda: f('"a\r\nb"') == [["a\r\nb"]]),
        ('escaped quote "" -> "', lambda: f('"a""b"') == [['a"b']]),
        ("all-quotes empty field", lambda: f('""') == [[""]]),
        ("unquoted spaces preserved", lambda: f("a , b ") == [["a ", " b "]]),
        ("lenient concat \"a\"b -> ab", lambda: f('"a"b') == [["ab"]]),
        ("unterminated quote lenient", lambda: f('"abc') == [["abc"]]),
        ("multi field record", lambda: f("1,2,3,4") == [["1", "2", "3", "4"]]),
        ("quoted then comma then plain", lambda: f('"x",y') == [["x", "y"]]),
        ("empty fields ,, -> three empty", lambda: f(",,") == [["", "", ""]]),
        ("crlf and lf mixed", lambda: f("a\r\nb\nc") == [["a"], ["b"], ["c"]]),
        ("quoted field with comma and quote", lambda: f('"a,""b"""') == [['a,"b"']]),
        ("record with single empty via blank", lambda: f("\n") == [[""]]),
        ("no trailing sep two cols", lambda: f("k,v") == [["k", "v"]]),
    ]
def main():
    try:
        m = load(sys.argv[1]); f = getattr(m, "parse_csv")
    except Exception as e:
        print(f"FAIL load/parse_csv missing: {e}"); print("gate: 0/25"); return
    passed = 0; cs = checks(f)
    for desc, fn in cs:
        try: ok = bool(fn())
        except Exception: ok = False
        if ok: passed += 1
        else: print(f"FAIL {desc}")
    print(f"gate: {passed}/{len(cs)}")
if __name__ == "__main__": main()
