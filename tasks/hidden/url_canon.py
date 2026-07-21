#!/usr/bin/env python3
# HIDDEN mutation gate — adversarial checks NEVER shown to the builder.
import sys, importlib.util
def load(path):
    spec = importlib.util.spec_from_file_location("hcand_uc", path); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m
def checks(f):
    return [
        ("host lower but path case preserved",
         lambda: f("HTTPS://API.EXAMPLE.COM:443/PATH") == "https://api.example.com/PATH"),
        ("multi dotdot resolves", lambda: f("http://h/a/b/c/../../d") == "http://h/a/d"),
        ("dotdot beyond root clamps", lambda: f("http://h/../../x") == "http://h/x"),
        ("query not path-normalized", lambda: f("http://h/a?b=/c/../d") == "http://h/a?b=/c/../d"),
        ("fragment hex uppercased", lambda: f("http://h/p#a%2f") == "http://h/p#a%2F"),
        ("443 non-default for http kept", lambda: f("http://h:443/") == "http://h:443/"),
        ("max port 65535 kept", lambda: f("http://h:65535/") == "http://h:65535/"),
        ("already-upper hex unchanged", lambda: f("http://h/%41") == "http://h/%41"),
        ("empty path with query -> /", lambda: f("http://h?x=1") == "http://h/?x=1"),
        ("trailing dotdot dir slash", lambda: f("http://h/a/b/..") == "http://h/a/"),
        ("80 non-default for https kept", lambda: f("https://h:80/") == "https://h:80/"),
        ("reject scheme-relative //h", lambda: f("//h/path") is None),
    ]
def main():
    try:
        m = load(sys.argv[1]); f = getattr(m, "canonicalize")
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
