#!/usr/bin/env python3
"""Merge the shipped result JSONs (results-full.json + results-pass2.json overriding, plus the
anvil-v3 and fable re-run cells) and print the ranked v1.7 tables. Writes the regenerated markdown
table to results/table-regen.md so the shipped evidence (results/table.md) is never overwritten.

Note: the shipped results/table.md is the 20-lane v1.7 snapshot (full + pass2). Regenerating here
also surfaces three post-hoc partial probe lanes from the small re-run JSONs — anvil-v3 (2/5
cells), anvil-ultra (1/5 cells), fable-5-bare (an OpenRouter retry of the fable-5 router-bug
lane) — which were not part of the published 20-lane table. All 20 shared lanes reproduce the
shipped table's numbers exactly."""
import json
import os

D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def load():
    cells = {}
    for fn in ["results-full.json", "results-pass2.json", "results-anvil3.json", "results-fable.json"]:
        p = os.path.join(D, fn)
        if not os.path.exists(p):
            continue
        for r in json.load(open(p)):
            cells[(r["lane"], r["task"])] = r    # pass2 overrides full
    return cells


def main():
    cells = load()
    lanes = sorted({k[0] for k in cells})
    tasks = ["expr_interp", "csv_parse", "semver_cmp", "toposort", "url_canon"]
    rows = []
    for lane in lanes:
        vps, hps, js, costs, n = [], [], [], 0.0, 0
        for t in tasks:
            c = cells.get((lane, t))
            if not c:
                continue
            n += 1
            if c.get("ok"):
                vps.append(c["visible_pct"])
                hps.append(c["hidden_pct"])
                if c["judge"]["overall"] is not None:
                    js.append(c["judge"]["overall"])
                costs += c.get("cost", 0.0)
            else:
                vps.append(0)
                hps.append(0)
                js.append(c["judge"]["overall"] if c.get("judge") else 0)
                costs += c.get("cost", 0.0)
        if not n:
            continue
        rows.append({
            "lane": lane, "n": n,
            "visible": round(sum(vps) / n, 1), "hidden": round(sum(hps) / n, 1),
            "judge": round(sum(js) / len(js), 2) if js else None, "cost": round(costs, 5),
        })
    # attach a 'via' per lane (flux/openrouter/system)
    for r in rows:
        vias = {cells[(r["lane"], t)].get("via") for t in tasks if (r["lane"], t) in cells}
        r["via"] = next((v for v in ("openrouter", "system") if v in vias), "flux")
    # rank: visible desc, then hidden desc, then judge desc, then cost asc
    rows.sort(key=lambda r: (-r["visible"], -r["hidden"], -(r["judge"] or 0), r["cost"]))
    print(f"\n=== v1.7 RANKED ({len(rows)} lanes, {len(tasks)} tasks) — avg across tasks ===")
    print(f"{'lane':16s} {'vis%':>5s} {'hid%':>5s} {'judge':>6s} {'$total':>9s}  cells via")
    for r in rows:
        print(f"{r['lane']:16s} {r['visible']:5.0f} {r['hidden']:5.0f} "
              f"{(r['judge'] if r['judge'] is not None else 0):6.2f} {r['cost']:9.5f}  {r['n']}/5 {r['via']}")
    # markdown for the writeup
    md = ["| lane | via | visible% | hidden% | judge | $ (5 tasks) | cells |",
          "|---|---|---:|---:|---:|---:|---:|"]
    for r in rows:
        j = f"{r['judge']:.2f}" if r['judge'] is not None else "—"
        md.append(f"| {r['lane']} | {r['via']} | {r['visible']:.0f} | {r['hidden']:.0f} | {j} | {r['cost']:.5f} | {r['n']}/5 |")
    open(os.path.join(D, "table-regen.md"), "w").write("\n".join(md) + "\n")
    # per-task visible%
    print("\n=== per-task VISIBLE% ===")
    print(f"{'lane':16s} " + " ".join(f"{t[:9]:>9s}" for t in tasks))
    for lane in [r["lane"] for r in rows]:
        cellstr = []
        for t in tasks:
            c = cells.get((lane, t))
            cellstr.append(f"{c['visible_pct']:>9d}" if c and c.get("ok") else ("     FAIL" if c else "        -"))
        print(f"{lane:16s} " + " ".join(cellstr))


if __name__ == "__main__":
    main()
