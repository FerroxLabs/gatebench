#!/usr/bin/env python3
"""GATEBENCH public runner — reproduce solo-model lanes via OpenRouter, score both machine gates.

For each (lane, task): request one complete single-file Python solution from the model, then score
it on the two machine axes — the VISIBLE gate (tasks/gates/<task>.py, part of the spec contract)
and the HIDDEN mutation gate (tasks/hidden/<task>.py, never shown to the builder).

Requires: OPENROUTER_API_KEY in the environment (no key files are read).
Endpoint: https://openrouter.ai/api/v1/chat/completions (real retail cost via usage.cost).

Usage:
  python runners/run_bench.py                                # all named OpenRouter lanes x 5 tasks
  python runners/run_bench.py --lane deepseek-v4-pro         # one named lane
  python runners/run_bench.py --lane vendor/some-model       # any raw OpenRouter slug
  python runners/run_bench.py --lane gate-first              # product lane: static evidence, no-op
  python runners/run_bench.py --tasks expr_interp,url_canon --out results/results-local.json

Note on the gate-first lane: the gate-first executor is the PRODUCT UNDER TEST and its
implementation is not in this repository. Its cells ship as static evidence in results/
(including full climb traces in `anvil_log` and embedded generated code in
results-objective.json, independently re-checkable with verify/verify_results.py).
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
TASKS = ["expr_interp", "csv_parse", "semver_cmp", "toposort", "url_canon"]
BUILD_SYS = ("Provide the complete single self-contained Python 3 file (stdlib only, shebang first). "
             "You may reason first if needed, but END your response with the full file in ONE "
             "```python fenced code block.")

# Named lanes that were measured via OpenRouter in the v1.7 run (third-party reproducible).
# Any other OpenRouter slug can be passed directly with --lane vendor/model.
OR_LANES = {
    "deepseek-v4-pro": "deepseek/deepseek-v4-pro",
    "gemini-3-1-pro": "google/gemini-3.1-pro-preview",
    "claude-sonnet-5": "anthropic/claude-sonnet-5",
    "kimi-k3": "moonshotai/kimi-k3",
    "glm-5-2": "z-ai/glm-5.2",
}

GATE_FIRST_NOTE = (
    "gate-first lane: static evidence — the gate-first executor is the product under test and its\n"
    "implementation is not in this repository. Its measured cells (scores, costs, climb traces,\n"
    "and embedded generated code) ship in results/ and are re-checkable offline with\n"
    "  python verify/verify_results.py\n"
    "See METHODOLOGY.md and MODELS.md for what is and is not third-party reproducible."
)


def _key():
    k = os.environ.get("OPENROUTER_API_KEY")
    if not k:
        raise RuntimeError("set OPENROUTER_API_KEY in the environment")
    return k


def _extract_code(text):
    """Pull the FINAL python file out of a reply (reasoning models think first, then emit code):
    prefer the LAST fenced block that contains def/import; else the longest fenced block; else raw."""
    if not text:
        return ""
    if "```" in text:
        parts = text.split("```")
        blocks = []
        for i in range(1, len(parts), 2):
            b = parts[i]
            nl = b.find("\n")
            head = (b[:nl].strip().lower() if nl >= 0 else "")
            body = b[nl + 1:] if (nl >= 0 and head in ("python", "py", "python3")) else b
            blocks.append(body)
        for b in reversed(blocks):  # the LAST real code block = the final answer
            if "def " in b or "import " in b or b.lstrip().startswith("#!"):
                return b.strip() + "\n"
        if blocks:
            return max(blocks, key=len).strip() + "\n"
    return text.strip() + "\n"


def chat(model, messages, max_tokens=32000):
    body = json.dumps({"model": model, "max_tokens": max_tokens, "messages": messages,
                       "usage": {"include": True}}).encode()
    headers = {"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"}
    last = {"ok": False, "model": model, "error": "no attempt"}
    for attempt in range(4):
        req = urllib.request.Request(ENDPOINT, data=body, headers=headers, method="POST")
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                d = json.loads(resp.read().decode())
            ch = (d.get("choices") or [{}])[0]
            msg = ch.get("message") or {}
            content = msg.get("content") or msg.get("reasoning") or ""
            usage = d.get("usage") or {}
            return {"ok": True, "model": model, "content": content, "code": _extract_code(content),
                    "finish": ch.get("finish_reason"), "cost": usage.get("cost"),
                    "out_tok": usage.get("completion_tokens"), "latency": round(time.time() - t0, 1)}
        except urllib.error.HTTPError as e:
            last = {"ok": False, "model": model, "status": e.code, "error": e.read().decode()[:200]}
            if e.code in (429, 502, 503) and attempt < 3:
                time.sleep(20)
                continue
            return last
        except Exception as e:
            last = {"ok": False, "model": model, "error": repr(e)}
            if attempt < 3:
                time.sleep(10)
                continue
            return last
    return last


def spec_of(task):
    return open(os.path.join(ROOT, "tasks", "specs", f"{task}.md")).read()


def _run_gate(gate_path, code, prefix):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
        tf.write(code or "")
        p = tf.name
    try:
        r = subprocess.run([sys.executable, gate_path, p], capture_output=True, text=True, timeout=60)
        out = r.stdout + r.stderr
    except Exception as e:
        os.unlink(p)
        return (0, 1, f"err:{e}")
    n = m = 0
    for line in out.splitlines():
        if line.startswith(prefix + ":"):
            try:
                n, m = (int(x) for x in line.split(":")[1].strip().split("/"))
            except Exception:
                pass
    os.unlink(p)
    return (n, m, out)


def score_axes(task, code):
    vn, vm, _ = _run_gate(os.path.join(ROOT, "tasks", "gates", f"{task}.py"), code, "gate")
    hn, hm, _ = _run_gate(os.path.join(ROOT, "tasks", "hidden", f"{task}.py"), code, "hidden")
    return {"visible": [vn, vm], "hidden": [hn, hm]}


def compiles(code):
    try:
        compile(code or "", "<c>", "exec")
        return True
    except Exception:
        return False


def cell(lane, slug, task, max_tokens):
    print(f"  [{lane} / {task}] building...", flush=True)
    spec = spec_of(task)
    msgs = [{"role": "system", "content": BUILD_SYS}, {"role": "user", "content": spec}]
    r = chat(slug, msgs, max_tokens=max_tokens)
    if not r["ok"]:
        print(f"    BUILD FAIL: {str(r.get('error'))[:120]}", flush=True)
        return {"lane": lane, "task": task, "ok": False, "err": str(r.get("error"))[:200],
                "cost": 0.0, "via": "openrouter"}
    axes = score_axes(task, r["code"])
    vp = round(100 * axes["visible"][0] / max(1, axes["visible"][1]))
    hp = round(100 * axes["hidden"][0] / max(1, axes["hidden"][1]))
    truncated = (r.get("finish") == "length") or not compiles(r["code"])
    print(f"    visible {axes['visible'][0]}/{axes['visible'][1]} ({vp}%)  "
          f"hidden {axes['hidden'][0]}/{axes['hidden'][1]} ({hp}%)  "
          f"cost ${(r['cost'] or 0.0):.5f}  finish:{r.get('finish')}", flush=True)
    return {"lane": lane, "task": task, "ok": True, "visible": axes["visible"],
            "hidden": axes["hidden"], "visible_pct": vp, "hidden_pct": hp,
            "cost": r["cost"] or 0.0, "finish": r.get("finish"), "truncated": truncated,
            "code": r["code"], "via": "openrouter"}


def main():
    ap = argparse.ArgumentParser(description="GATEBENCH public runner (OpenRouter lanes)")
    ap.add_argument("--lane", help="named lane, raw OpenRouter slug, or 'gate-first'")
    ap.add_argument("--tasks", help=f"comma-separated subset of {','.join(TASKS)}")
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "results-local.json"),
                    help="output JSON (default results/results-local.json; never overwrites shipped evidence)")
    ap.add_argument("--max-tokens", type=int, default=32000)
    args = ap.parse_args()

    if args.lane == "gate-first":
        print(GATE_FIRST_NOTE)
        return

    if args.lane:
        lanes = {args.lane: OR_LANES.get(args.lane, args.lane)}
    else:
        lanes = dict(OR_LANES)
    tasks = args.tasks.split(",") if args.tasks else TASKS
    for t in tasks:
        if t not in TASKS:
            sys.exit(f"unknown task: {t} (choose from {TASKS})")

    results = json.load(open(args.out)) if os.path.exists(args.out) else []
    done = {(r["lane"], r["task"]) for r in results}
    for task in tasks:
        for lane, slug in lanes.items():
            if (lane, task) in done:
                continue
            try:
                results.append(cell(lane, slug, task, args.max_tokens))
            except Exception as e:
                print(f"    CELL ERROR: {e}", flush=True)
                results.append({"lane": lane, "task": task, "ok": False, "err": repr(e)[:200]})
            json.dump(results, open(args.out, "w"), indent=2)
    print(f"\nDONE. {sum(1 for r in results if r.get('ok'))}/{len(results)} cells ok -> {args.out}",
          flush=True)


if __name__ == "__main__":
    main()
