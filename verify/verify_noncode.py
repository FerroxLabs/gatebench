#!/usr/bin/env python3
"""GATEBENCH non-code verifiability: re-check results/results-noncode.json offline.

results/results-noncode.json embeds the ACTUAL generated artifact for every cell of the
non-code run (3 lanes x 2 tasks) plus the hidden-gate validation fixtures (known-good
reference and fluent-but-wrong mutant per task). This script re-runs each task's VISIBLE
gate (tasks/noncode/gates/<task>.py) and HIDDEN gate (tasks/noncode/hidden/<task>.py)
against every embedded artifact, pure stdlib, no network, no API key, and asserts:

  1. every cell's recomputed visible/hidden counts and percentages match the recorded
     values exactly (same rounding as the measurement run: round(100*n/max(1,m)));
  2. every validation fixture behaves as recorded AND as designed: the reference passes
     both gates in full; the mutant passes the visible gate in full and drops on hidden.

Exit status: 0 iff everything re-verifies. Any mismatch exits nonzero.
Usage: python verify/verify_noncode.py
"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results", "results-noncode.json")


def gate_counts(gate_path, artifact, prefix):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
        tf.write(artifact or "")
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
                return [n, m], f"{n}/{m}"
            except Exception:
                pass
    return None, "no score line emitted"


def rescore(task, artifact):
    v, vd = gate_counts(os.path.join(ROOT, "tasks", "noncode", "gates", f"{task}.py"),
                        artifact, "gate")
    h, hd = gate_counts(os.path.join(ROOT, "tasks", "noncode", "hidden", f"{task}.py"),
                        artifact, "hidden")
    return v, h, vd, hd


def main():
    doc = json.load(open(RESULTS))
    bad = []

    print("validation fixtures:")
    for rec in doc["gate_validation"]:
        task, fixture = rec["task"], rec["fixture"]
        v, h, vd, hd = rescore(task, rec["artifact"])
        ok = (v == rec["visible"]) and (h == rec["hidden"])
        if fixture == "reference":
            designed = v is not None and h is not None and v[0] == v[1] and h[0] == h[1]
        else:
            designed = v is not None and h is not None and v[0] == v[1] and h[0] < h[1]
        tag = "VERIFIED " if (ok and designed) else "MISMATCH"
        print(f"  {tag} {task:18s} {fixture:9s} visible {vd} (recorded {rec['visible']})  "
              f"hidden {hd} (recorded {rec['hidden']})")
        if not (ok and designed):
            bad.append(f"validation {task}/{fixture}")

    print("cells:")
    for c in doc["cells"]:
        lane, task = c["lane"], c["task"]
        v, h, vd, hd = rescore(task, c["artifact"])
        vp = None if v is None else round(100 * v[0] / max(1, v[1]))
        hp = None if h is None else round(100 * h[0] / max(1, h[1]))
        ok = (v == c["visible"] and h == c["hidden"]
              and vp == c["visible_pct"] and hp == c["hidden_pct"])
        tag = "VERIFIED " if ok else "MISMATCH"
        print(f"  {tag} {lane:16s} {task:18s} visible {vd} -> {vp}% (recorded "
              f"{c['visible_pct']}%)  hidden {hd} -> {hp}% (recorded {c['hidden_pct']}%)")
        if not ok:
            bad.append(f"cell {lane}/{task}")

    n = len(doc["gate_validation"]) + len(doc["cells"])
    print(f"\n{n} embedded artifacts checked: {n - len(bad)} verified, {len(bad)} mismatched.")
    if bad:
        print("MISMATCHES: " + ", ".join(bad))
        sys.exit(1)
    print("All recorded non-code gate scores reproduce from the embedded artifacts. Evidence verified.")


if __name__ == "__main__":
    main()
