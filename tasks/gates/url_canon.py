#!/usr/bin/env python3
import sys, importlib.util
def load(path):
    spec = importlib.util.spec_from_file_location("cand_uc", path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m
def checks(f):
    return [
        ("lowercase scheme+host", lambda: f("HTTP://Example.COM/") == "http://example.com/"),
        ("drop default http port 80", lambda: f("http://h:80/a") == "http://h/a"),
        ("drop default https port 443", lambda: f("https://h:443/a") == "https://h/a"),
        ("keep non-default port", lambda: f("http://h:8080/a") == "http://h:8080/a"),
        ("strip leading zeros non-default port", lambda: f("https://h:08080/a") == "https://h:8080/a"),
        ("no path -> /", lambda: f("http://h") == "http://h/"),
        ("remove '.' segment", lambda: f("http://h/a/./b") == "http://h/a/b"),
        ("resolve '..' segment", lambda: f("http://h/a/../b") == "http://h/b"),
        ("clamp '..' at root", lambda: f("http://h/../a") == "http://h/a"),
        ("collapse duplicate slashes", lambda: f("http://h/a//b") == "http://h/a/b"),
        ("preserve trailing slash", lambda: f("http://h/a/") == "http://h/a/"),
        ("trailing '.' -> dir slash", lambda: f("http://h/a/.") == "http://h/a/"),
        ("'..' to root dir -> /", lambda: f("http://h/a/..") == "http://h/"),
        ("uppercase percent hex in path", lambda: f("http://h/a%2fb") == "http://h/a%2Fb"),
        ("preserve non-empty query", lambda: f("http://h/p?x=1") == "http://h/p?x=1"),
        ("drop empty query", lambda: f("http://h/p?") == "http://h/p"),
        ("drop empty fragment", lambda: f("http://h/p#") == "http://h/p"),
        ("preserve non-empty fragment", lambda: f("http://h/p#sec") == "http://h/p#sec"),
        ("uppercase percent hex in query", lambda: f("http://h/p?a=%3d") == "http://h/p?a=%3D"),
        ("path+query+frag together", lambda: f("http://H/a/./b?q=1#f") == "http://h/a/b?q=1#f"),
        ("reject userinfo", lambda: f("http://user@h/") is None),
        ("reject non-http scheme ftp", lambda: f("ftp://h/") is None),
        ("reject javascript scheme", lambda: f("javascript:alert(1)") is None),
        ("reject relative path", lambda: f("/path/only") is None),
        ("reject empty host", lambda: f("http:///path") is None),
        ("reject out-of-range port", lambda: f("http://h:99999/") is None),
        ("reject non-numeric port", lambda: f("http://h:80a/") is None),
        ("reject port zero", lambda: f("http://h:0/") is None),
        ("reject single-slash scheme sep", lambda: f("http:/h/") is None),
    ]
def main():
    try:
        m = load(sys.argv[1]); f = getattr(m, "canonicalize")
    except Exception as e:
        print(f"FAIL load/canonicalize missing: {e}"); print("gate: 0/29"); return
    passed = 0; cs = checks(f)
    for desc, fn in cs:
        try: ok = bool(fn())
        except Exception: ok = False
        if ok: passed += 1
        else: print(f"FAIL {desc}")
    print(f"gate: {passed}/{len(cs)}")
if __name__ == "__main__": main()
