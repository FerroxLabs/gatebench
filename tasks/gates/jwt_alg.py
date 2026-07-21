#!/usr/bin/env python3
import sys, importlib.util
def load(p):
    s=importlib.util.spec_from_file_location("c",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def checks(f):
    return [
        ("accept RS256", lambda: f('{"alg":"RS256"}')=="RS256"),
        ("accept ES256", lambda: f('{"alg":"ES256"}')=="ES256"),
        ("accept RS256 with extra fields", lambda: f('{"alg":"RS256","kid":"x"}')=="RS256"),
        ("SECURITY reject alg none", lambda: f('{"alg":"none"}') is None),
        ("SECURITY reject alg None", lambda: f('{"alg":"None"}') is None),
        ("SECURITY reject alg NONE", lambda: f('{"alg":"NONE"}') is None),
        ("SECURITY reject alg nOnE", lambda: f('{"alg":"nOnE"}') is None),
        ("SECURITY reject HS256 downgrade", lambda: f('{"alg":"HS256"}') is None),
        ("reject wrong case rs256", lambda: f('{"alg":"rs256"}') is None),
        ("reject trailing space 'RS256 '", lambda: f('{"alg":"RS256 "}') is None),
        ("reject missing alg", lambda: f('{"kid":"x"}') is None),
        ("SECURITY reject non-string alg number", lambda: f('{"alg":123}') is None),
        ("reject non-string alg list", lambda: f('{"alg":["RS256"]}') is None),
        ("reject malformed json", lambda: f('not json') is None),
        ("reject empty", lambda: f('') is None),
    ]
def main():
    try:
        m=load(sys.argv[1]); f=getattr(m,"choose_verifier")
    except Exception as e:
        print(f"FAIL load/choose_verifier missing: {e}"); print("gate: 0/15"); return
    p=0; cs=checks(f)
    for d,fn in cs:
        try: ok=bool(fn())
        except Exception: ok=False
        if ok: p+=1
        else: print(f"FAIL {d}")
    print(f"gate: {p}/{len(cs)}")
if __name__=="__main__": main()
