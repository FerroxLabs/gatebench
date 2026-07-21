#!/usr/bin/env python3
"""Objective code-quality pipeline — the un-gameable substance metrics (vs the surface LLM-judge).
Mirrors the format->lint->security->complexity->runtime pipeline used for the v1.7 objective re-score.

format_code : black (style normalized; equalizes cosmetics BEFORE any comparison)
lint        : ruff violation count (unused vars, shadowing, real smells — NOT just style)
security    : bandit issue counts by severity (eval/injection/unsafe)
complexity  : radon cyclomatic (avg/max), Maintainability Index, SLOC
runtime     : execute the solution's function on a stress workload, measure wall-time (efficiency)

Requires: pip install -r requirements.txt (black, radon, ruff, bandit).
Usage:    python runners/quality.py <candidate.py> <task>
"""
import json
import os
import subprocess
import sys
import tempfile
import time  # noqa: F401  (kept for parity with the measurement-run module)

import black
from radon.complexity import cc_visit
from radon.metrics import mi_visit
from radon.raw import analyze


def _tmp(code):
    tf = tempfile.NamedTemporaryFile("w", suffix=".py", delete=False)
    tf.write(code or "")
    tf.close()
    return tf.name


def format_code(code):
    try:
        f = black.format_str(code, mode=black.Mode(line_length=100))
        return f, (f != code)
    except Exception:
        return code, False


def lint_count(code):
    p = _tmp(code)
    r = subprocess.run(["ruff", "check", "--output-format=json", "--isolated", p],
                       capture_output=True, text=True)
    os.unlink(p)
    try:
        return len(json.loads(r.stdout or "[]"))
    except Exception:
        return -1


def security(code):
    p = _tmp(code)
    r = subprocess.run(["bandit", "-f", "json", "-q", p], capture_output=True, text=True)
    os.unlink(p)
    sev = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    try:
        for x in json.loads(r.stdout or "{}").get("results", []):
            s = x.get("issue_severity", "LOW").upper()
            sev[s] = sev.get(s, 0) + 1
    except Exception:
        pass
    return sev


def complexity(code):
    try:
        ccs = cc_visit(code)
        avg = round(sum(c.complexity for c in ccs) / len(ccs), 2) if ccs else 0
        mx = max((c.complexity for c in ccs), default=0)
        mi = round(mi_visit(code, True), 1)
        sloc = analyze(code).sloc
        return {"avg_cc": avg, "max_cc": mx, "mi": mi, "sloc": sloc}
    except Exception as e:
        return {"error": str(e)[:60]}


# Per-task stress workload: (func, driver-that-calls-it-hard). Driver runs in a subprocess against the
# candidate file; prints elapsed ms. Bounded by timeout — an infinite loop => runtime=None (not a hang).
WORKLOADS = {
    "expr_interp": ("run_program",
                    "progs=['a=1;'+';'.join(f'a=a*2+{i}%3-{i}//4' for i in range(1,120))]*400\n"
                    "for p in progs: f(p)"),
    "csv_parse": ("parse_csv",
                  "data='\\n'.join('\"x,y\",'+str(i)+',\"a\"\"b\",plain'+str(i) for i in range(4000))\n"
                  "for _ in range(60): f(data)"),
    "semver_cmp": ("compare",
                   "import itertools\nvs=[f'{a}.{b}.{c}-alpha.{d}' for a in range(3) for b in range(3) "
                   "for c in range(3) for d in range(4)]\n"
                   "for _ in range(40):\n for a,b in itertools.product(vs, vs[:20]): f(a,b)"),
    "toposort": ("toposort",
                 "g={str(i):[str(j) for j in range(max(0,i-3),i)] for i in range(400)}\n"
                 "for _ in range(300): f(g)"),
    "url_canon": ("canonicalize",
                  "urls=['http://Ex.com:80/a/./b/../c%2fd?x=1#f','https://h/'+'a/../'*30+'z']*3000\n"
                  "for u in urls: f(u)"),
}


def runtime_ms(code, task):
    if task not in WORKLOADS:
        return None
    func, driver = WORKLOADS[task]
    p = _tmp(code)
    runner = (f"import importlib.util,time,sys\n"
              f"spec=importlib.util.spec_from_file_location('c',{p!r});m=importlib.util.module_from_spec(spec)\n"
              f"spec.loader.exec_module(m); f=getattr(m,{func!r})\n"
              f"t=time.perf_counter()\n{driver}\n"
              f"print(round((time.perf_counter()-t)*1000,1))\n")
    try:
        r = subprocess.run([sys.executable, "-c", runner], capture_output=True, text=True, timeout=40)
        os.unlink(p)
        return float(r.stdout.strip().splitlines()[-1]) if r.stdout.strip() else None
    except Exception:
        try:
            os.unlink(p)
        except Exception:
            pass
        return None


def profile(code, task):
    """Full objective profile of a candidate (formatting normalized first)."""
    fmt, changed = format_code(code)
    return {
        "fmt_changed": changed,            # was the raw output already clean? (model discipline proxy)
        "lint": lint_count(fmt),           # real smells after formatting
        "security": security(fmt),         # bandit severities
        "complexity": complexity(fmt),     # radon CC/MI/SLOC
        "runtime_ms": runtime_ms(fmt, task),
    }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("usage: python runners/quality.py <candidate.py> <task>")
    print(json.dumps(profile(open(sys.argv[1]).read(), sys.argv[2]), indent=2))
