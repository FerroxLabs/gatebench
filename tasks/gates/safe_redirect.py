#!/usr/bin/env python3
import sys, importlib.util
def load(p):
    s=importlib.util.spec_from_file_location("c",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
A="allowed.com"
def checks(f):
    return [
        ("accept relative /dashboard", lambda: f(A,"/dashboard")=="/dashboard"),
        ("accept relative with query /a/b?x=1", lambda: f(A,"/a/b?x=1")=="/a/b?x=1"),
        ("accept same-host https", lambda: f(A,"https://allowed.com/path")=="https://allowed.com/path"),
        ("accept same-host http", lambda: f(A,"http://allowed.com")=="http://allowed.com"),
        ("accept case-insensitive host+scheme", lambda: f(A,"HTTPS://ALLOWED.COM/x")=="HTTPS://ALLOWED.COM/x"),
        ("SECURITY reject scheme-relative //evil.com", lambda: f(A,"//evil.com/x") is None),
        ("SECURITY reject backslash /\\evil.com", lambda: f(A,"/\\evil.com") is None),
        ("SECURITY reject other host https://evil.com", lambda: f(A,"https://evil.com/x") is None),
        ("SECURITY reject userinfo https://allowed.com@evil.com", lambda: f(A,"https://allowed.com@evil.com") is None),
        ("SECURITY reject suffix https://allowed.com.evil.com", lambda: f(A,"https://allowed.com.evil.com") is None),
        ("reject subdomain https://sub.allowed.com", lambda: f(A,"https://sub.allowed.com") is None),
        ("SECURITY reject javascript: scheme", lambda: f(A,"javascript:alert(1)") is None),
        ("reject data: scheme", lambda: f(A,"data:text/html,x") is None),
        ("reject empty", lambda: f(A,"") is None),
        ("SECURITY reject newline in target", lambda: f(A,"/a\nb") is None),
        ("reject tab in target", lambda: f(A,"https://allowed.com/a\tb") is None),
    ]
def main():
    try:
        m=load(sys.argv[1]); f=getattr(m,"is_safe_redirect")
    except Exception as e:
        print(f"FAIL load/is_safe_redirect missing: {e}"); print("gate: 0/16"); return
    p=0; cs=checks(f)
    for d,fn in cs:
        try: ok=bool(fn())
        except Exception: ok=False
        if ok: p+=1
        else: print(f"FAIL {d}")
    print(f"gate: {p}/{len(cs)}")
if __name__=="__main__": main()
