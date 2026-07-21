#!/usr/bin/env python3
import sys, importlib.util
def load(p):
    s=importlib.util.spec_from_file_location("c",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def checks(f):
    return [
        ("empty->b''", lambda: f("")==b""),
        ("QQ==->A", lambda: f("QQ==")==b"A"),
        ("QUI=->AB", lambda: f("QUI=")==b"AB"),
        ("QUJD->ABC", lambda: f("QUJD")==b"ABC"),
        ("aGVsbG8=->hello", lambda: f("aGVsbG8=")==b"hello"),
        ("reject len2 QQ", lambda: f("QQ") is None),
        ("reject len3 QQ=", lambda: f("QQ=") is None),
        ("reject len5 QQ===", lambda: f("QQ===") is None),
        ("reject ====", lambda: f("====") is None),
        ("reject bad char QUJD!", lambda: f("QUJD!") is None),
        ("reject data-after-pad QQ=A", lambda: f("QQ=A") is None),
        ("reject interior pad Q=JD", lambda: f("Q=JD") is None),
        ("reject all-bad @@@@", lambda: f("@@@@") is None),
        ("reject len6 QUJDQQ", lambda: f("QUJDQQ") is None),
    ]
def main():
    try:
        m=load(sys.argv[1]); f=getattr(m,"b64decode_strict")
    except Exception as e:
        print(f"FAIL load/b64decode_strict missing: {e}"); print("gate: 0/14"); return
    p=0; cs=checks(f)
    for d,fn in cs:
        try: ok=bool(fn())
        except Exception: ok=False
        if ok: p+=1
        else: print(f"FAIL {d}")
    print(f"gate: {p}/{len(cs)}")
if __name__=="__main__": main()
