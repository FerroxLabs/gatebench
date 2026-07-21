#!/usr/bin/env python3
import sys, importlib.util
def load(p):
    s=importlib.util.spec_from_file_location("c",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
def checks(f):
    return [
        ("I->1", lambda: f("I")==1), ("III->3", lambda: f("III")==3),
        ("IV->4", lambda: f("IV")==4), ("IX->9", lambda: f("IX")==9),
        ("XL->40", lambda: f("XL")==40), ("XC->90", lambda: f("XC")==90),
        ("CD->400", lambda: f("CD")==400), ("CM->900", lambda: f("CM")==900),
        ("MCMXCIV->1994", lambda: f("MCMXCIV")==1994),
        ("MMMCMXCIX->3999", lambda: f("MMMCMXCIX")==3999),
        ("reject IIII", lambda: f("IIII") is None),
        ("reject VV", lambda: f("VV") is None),
        ("reject IL", lambda: f("IL") is None),
        ("reject IC", lambda: f("IC") is None),
        ("reject XM", lambda: f("XM") is None),
        ("reject VX", lambda: f("VX") is None),
        ("reject MMMM (>3999)", lambda: f("MMMM") is None),
        ("reject empty", lambda: f("") is None),
        ("reject lowercase iv", lambda: f("iv") is None),
        ("reject junk A", lambda: f("A") is None),
    ]
def main():
    try:
        m=load(sys.argv[1]); f=getattr(m,"roman_parse")
    except Exception as e:
        print(f"FAIL load/roman_parse missing: {e}"); print("gate: 0/20"); return
    p=0; cs=checks(f)
    for d,fn in cs:
        try: ok=bool(fn())
        except Exception: ok=False
        if ok: p+=1
        else: print(f"FAIL {d}")
    print(f"gate: {p}/{len(cs)}")
if __name__=="__main__": main()
