#!/usr/bin/env python3
"""GATEBENCH verifiability centerpiece.

results/results-objective.json embeds the ACTUAL generated code for every successful cell of the
objective re-score run (4 lanes x 5 tasks). This script re-runs each task's VISIBLE gate
(tasks/gates/<task>.py) and HIDDEN gate (tasks/hidden/<task>.py) against that embedded code —
pure stdlib, no network, no API key — and asserts the recomputed percentages match the recorded
visible_pct / hidden_pct exactly (same rounding as the measurement run: round(100*n/max(1,m))).

Exit status: 0 iff every embedded-code cell re-verifies. Any mismatch exits nonzero.
Records without embedded code (build failures recorded as ok=false) are reported as skipped.

Usage: python verify/verify_results.py
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "results-objective.json")


def gate_pct(gate_path, code, prefix):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
        tf.write(code or "")
        p = tf.name
    try:
        r = subprocess.run([sys.executable, gate_path, p], capture_output=True, text=True, timeout=120)
        out = r.stdout + r.stderr
    except Exception as e:
        os.unlink(p)
        return None, f"gate error: {e}"
    os.unlink(p)
    for line in out.splitlines():
        if line.startswith(prefix + ":"):
            try:
                n, m = (int(x) for x in line.split(":")[1].strip().split("/"))
                return round(100 * n / max(1, m)), f"{n}/{m}"
            except Exception:
                pass
    return None, "no score line emitted"


def main():
    records = json.load(open(RESULTS))
    checked = mismatched = skipped = 0
    failures = []
    for r in records:
        lane, task = r.get("lane"), r.get("task")
        code = r.get("code")
        if not code:
            skipped += 1
            print(f"SKIP      {lane:14s} {task:12s} (no embedded code; recorded ok={r.get('ok')})")
            continue
        checked += 1
        vp, vdetail = gate_pct(os.path.join(ROOT, "tasks", "gates", f"{task}.py"), code, "gate")
        hp, hdetail = gate_pct(os.path.join(ROOT, "tasks", "hidden", f"{task}.py"), code, "hidden")
        ok = (vp == r.get("visible_pct")) and (hp == r.get("hidden_pct"))
        tag = "VERIFIED " if ok else "MISMATCH"
        print(f"{tag} {lane:14s} {task:12s} visible {vdetail} -> {vp}% (recorded {r.get('visible_pct')}%)  "
              f"hidden {hdetail} -> {hp}% (recorded {r.get('hidden_pct')}%)")
        if not ok:
            mismatched += 1
            failures.append((lane, task, vp, r.get("visible_pct"), hp, r.get("hidden_pct")))
    print(f"\n{checked} embedded-code cells checked: {checked - mismatched} verified, "
          f"{mismatched} mismatched, {skipped} skipped (no code).")
    if failures:
        print("MISMATCHES:")
        for f in failures:
            print(f"  {f[0]}/{f[1]}: visible {f[2]} vs recorded {f[3]}, hidden {f[4]} vs recorded {f[5]}")
        sys.exit(1)
    print("All recorded gate percentages reproduce from the embedded code. Evidence verified.")


if __name__ == "__main__":
    main()
