#!/usr/bin/env python3
"""Regenerate every chart in the README from the shipped results JSONs.

Pure stdlib, no network, no third-party imports. Output is deterministic: running this
script twice produces byte-identical SVGs, so any reader can regenerate the charts and
`git diff` to confirm the images match the shipped evidence.

    python assets/generate_charts.py

Charts written (all into assets/):

  cost-vs-correctness.svg   scatter over the 20-lane v1.7 fold (results-full.json +
                            results-pass2.json): x = measured avg cost per task (log),
                            y = avg visible-gate %. The two flagged lanes (fable-5:
                            router bug; hermes: empty/timeout, $0 spend) are excluded
                            and noted on the chart.
  objective-substance.svg   grouped bars from results-objective.json (4 lanes):
                            Maintainability Index (higher better) and measured
                            runtime ms (lower better), side-by-side panels.
  gate-lift.svg             the ungated -> gated lift: minimax-solo (the executor's
                            own first-probe model, run bare) vs Anvil (lane id anvil-v2), visible and
                            hidden gate averages from the same fold.

Aggregation matches runners/agg.py exactly (per-lane mean over the 5 v1.7 tasks;
failed cells score 0; costs summed as measured). The script asserts its own
aggregates against the shipped results/table.md and refuses to draw from numbers
that do not reproduce.
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
ASSETS = os.path.join(ROOT, "assets")
TASKS = ["expr_interp", "csv_parse", "semver_cmp", "toposort", "url_canon"]

# ---------------------------------------------------------------- palette (light surface)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BLUE = "#2a78d6"      # highlighted entity: the gate-first executor lane
GRAY = "#a3a29b"      # all other lanes
FONT = 'font-family="system-ui, -apple-system, Segoe UI, sans-serif"'


# ---------------------------------------------------------------- data
def load_fold():
    """20-lane fold: results-full.json + results-pass2.json (pass2 overrides), same as agg.py."""
    cells = {}
    for fn in ["results-full.json", "results-pass2.json"]:
        for r in json.load(open(os.path.join(RESULTS, fn))):
            cells[(r["lane"], r["task"])] = r
    lanes = {}
    for lane in sorted({k[0] for k in cells}):
        vps, hps, cost, via = [], [], 0.0, set()
        for t in TASKS:
            c = cells[(lane, t)]
            vps.append(c["visible_pct"] if c.get("ok") else 0)
            hps.append(c["hidden_pct"] if c.get("ok") else 0)
            cost += c.get("cost", 0.0)
            via.add(c.get("via"))
        lanes[lane] = {
            "visible": sum(vps) / len(TASKS),
            "hidden": sum(hps) / len(TASKS),
            "cost_total": cost,
            "cost_per_task": cost / len(TASKS),
            "via": next((v for v in ("openrouter", "system") if v in via), "flux"),
        }
    return lanes


def check_against_shipped_table(lanes):
    """Refuse to draw if our aggregates disagree with the shipped results/table.md."""
    shipped = {}
    for line in open(os.path.join(RESULTS, "table.md")):
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) < 6 or parts[0] in ("lane", "---"):
            continue
        try:
            shipped[parts[0]] = (int(parts[2]), int(parts[3]), float(parts[5]))
        except ValueError:
            continue
    bad = []
    for lane, (vis, hid, cost) in shipped.items():
        if lane not in lanes:
            bad.append(f"{lane}: in table.md but not in the JSONs")
            continue
        L = lanes[lane]
        if round(L["visible"]) != vis or round(L["hidden"]) != hid or abs(L["cost_total"] - cost) > 5e-6:
            bad.append(f"{lane}: JSON says {round(L['visible'])}/{round(L['hidden'])}/"
                       f"{L['cost_total']:.5f}, table.md says {vis}/{hid}/{cost:.5f}")
    if bad:
        raise SystemExit("aggregates do not reproduce results/table.md:\n  " + "\n  ".join(bad))
    print(f"cross-check: {len(shipped)} lanes reproduce results/table.md exactly")


def load_objective():
    """Per-lane aggregates over completed cells of results-objective.json."""
    recs = json.load(open(os.path.join(RESULTS, "results-objective.json")))
    lanes = {}
    for r in recs:
        lanes.setdefault(r["lane"], []).append(r)
    out = {}
    for lane, rs in lanes.items():
        ok = [r for r in rs if r.get("ok")]
        mi = [r["profile"]["complexity"]["mi"] for r in ok]
        rt = [r["profile"]["runtime_ms"] for r in ok]
        out[lane] = {
            "cells": f"{len(ok)}/{len(rs)}",
            "mi": sum(mi) / len(mi),
            "rt": sum(rt) / len(rt),
            "cost": sum(r.get("cost") or 0.0 for r in rs),
        }
    return out


# ---------------------------------------------------------------- svg helpers
def svg_open(w, h, title):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{title}">',
            f'<rect width="{w}" height="{h}" fill="{SURFACE}"/>']


def text(x, y, s, size=12, fill=INK2, anchor="start", weight="normal"):
    w = f' font-weight="{weight}"' if weight != "normal" else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" {FONT} font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}"{w}>{s}</text>')


def money(v):
    return f"${v:.4f}" if v < 0.01 else f"${v:.3f}" if v < 0.1 else f"${v:.2f}"


# ---------------------------------------------------------------- chart 1: cost vs correctness
# label placement per lane: (dx, dy, anchor) relative to the point, hand-spaced so the
# fixed data positions never collide. Data positions themselves come only from the JSONs.
LABEL_POS = {
    # near row (16px off the point) and far row (30px) alternate through the dense
    # cluster of lanes sitting exactly at 100% so no two labels overlap.
    "anvil-v2":          (0, -16, "middle"),
    "minimax-solo":      (10, 4, "start"),
    "mistral-large":     (10, 4, "start"),
    "claude-haiku":      (10, 14, "start"),
    "gpt-5-6-luna":      (0, -30, "middle"),
    "glm-5-2":           (-8, 20, "end"),
    "qwen-plus":         (10, 4, "start"),
    "grok-4-5":          (0, 22, "middle"),
    "deepseek-v4-pro":   (-4, -16, "middle"),
    "opus-4-8":          (26, 20, "middle"),
    "fugu":              (14, -16, "middle"),
    "gpt-5-6-terra":     (14, -30, "middle"),
    "gpt-5-6-sol":       (-2, -16, "middle"),
    "claude-sonnet-5":   (2, 20, "middle"),
    "fugu-ultra":        (10, 4, "start"),
    "kimi-k3":           (-8, -16, "middle"),
    "gemini-3-1-pro":    (12, -30, "middle"),
    "openrouter-fusion": (-12, 4, "end"),
}


def chart_cost_vs_correctness(lanes):
    w, h = 920, 570
    ml, mr, mt, mb = 64, 30, 88, 84
    pw, ph = w - ml - mr, h - mt - mb
    # flagged lanes are excluded (fable-5: router content-filter bug, 0 is not capability;
    # hermes: empty/timeout with $0 measured spend, unplottable on a log cost axis)
    plot = {k: v for k, v in lanes.items() if k not in ("fable-5", "hermes")}
    xmin, xmax = math.log10(0.001), math.log10(0.5)
    ymin, ymax = 50.0, 103.0

    def X(c):
        return ml + (math.log10(c) - xmin) / (xmax - xmin) * pw

    def Y(v):
        return mt + (ymax - v) / (ymax - ymin) * ph

    s = svg_open(w, h, "Average cost per task (log scale) versus average visible-gate "
                       "percentage for 18 plotted lanes; the gate-first executor lane "
                       "the Anvil lane sits in the top-left corner at 100 percent for $0.0063 per task.")
    s.append(text(ml, 28, "Correctness vs. cost: 20-lane fold, 5 tasks, 133 visible checks",
                  16, INK, weight="600"))
    s.append(text(ml, 48, "Each point is one lane: avg visible-gate % (y) vs measured avg cost "
                          "per task (x, log scale). Top-left wins.", 12, INK2))
    s.append(text(ml, 64, "Excluded as flagged, not scored: fable-5 (router content-filter bug), "
                          "hermes (empty output, $0 measured spend).", 11, MUTED))
    # gridlines + axes
    for v in (50, 60, 70, 80, 90, 100):
        y = Y(v)
        s.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{ml + pw}" y2="{y:.1f}" '
                 f'stroke="{GRID}" stroke-width="1"/>')
        s.append(text(ml - 8, y + 4, str(v), 11, MUTED, anchor="end"))
    for c in (0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5):
        x = X(c)
        s.append(f'<line x1="{x:.1f}" y1="{mt}" x2="{x:.1f}" y2="{mt + ph}" '
                 f'stroke="{GRID}" stroke-width="1"/>')
        lab = f"${c:g}"
        s.append(text(x, mt + ph + 18, lab, 11, MUTED, anchor="middle"))
    s.append(f'<line x1="{ml}" y1="{mt + ph}" x2="{ml + pw}" y2="{mt + ph}" '
             f'stroke="{AXIS}" stroke-width="1"/>')
    s.append(text(ml + pw / 2, h - 40, "measured avg cost per task (USD, log scale)",
                  12, INK2, anchor="middle"))
    s.append(f'<text x="20" y="{mt + ph / 2:.1f}" {FONT} font-size="12" fill="{INK2}" '
             f'text-anchor="middle" transform="rotate(-90 20 {mt + ph / 2:.1f})">'
             f'avg visible-gate %</text>')
    # points, sorted for deterministic output
    for lane in sorted(plot):
        L = plot[lane]
        x, y = X(L["cost_per_task"]), Y(L["visible"])
        hot = lane == "anvil-v2"
        color = BLUE if hot else GRAY
        dx, dy, anchor = LABEL_POS[lane]
        if hot:
            s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="none" '
                     f'stroke="{BLUE}" stroke-width="1.5"/>')
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{color}" '
                 f'stroke="{SURFACE}" stroke-width="2"/>')
        disp = "Anvil" if lane == "anvil-v2" else lane
        label = f"{disp}  {money(L['cost_per_task'])}" if hot else disp
        s.append(text(x + dx, y + dy, label, 11, INK if hot else INK2, anchor=anchor,
                      weight="600" if hot else "normal"))
    s.append(text(ml + pw, h - 12, "generated by assets/generate_charts.py from "
                                   "results/results-full.json + results-pass2.json",
                  10, MUTED, anchor="end"))
    s.append("</svg>")
    return "\n".join(s) + "\n"


# ---------------------------------------------------------------- chart 2: objective substance
OBJ_ORDER = ["anvil-v2", "opus-4-8", "gpt-5-6-luna", "gpt-5-6-sol"]
OBJ_LABEL = {"anvil-v2": "Anvil (gate-first)", "opus-4-8": "opus-4.8",
             "gpt-5-6-luna": "gpt-5.6-luna", "gpt-5-6-sol": "gpt-5.6-sol"}


def chart_objective(obj):
    w, h = 920, 420
    panel_w, gap = 400, 60
    ml, mt, ph = 40, 96, 230
    s = svg_open(w, h, "Objective substance re-score: Anvil has the highest maintainability "
                       "index at 51.6 and the fastest measured runtime at 103.4 ms among the "
                       "four re-scored lanes.")
    s.append(text(ml, 28, "Objective substance: black-normalized, then measured "
                          "(results-objective.json)", 16, INK, weight="600"))
    s.append(text(ml, 48, "Formatting equalized with black before scoring. Anvil aggregates "
                          "cover its 3/5 completed cells (expr_interp and csv_parse", 12, INK2))
    s.append(text(ml, 64, "timed out at generation in this run and are recorded as failures); "
                          "the other lanes cover 5/5. Runtime is a per-task stress workload.", 12, INK2))

    def panel(x0, title, key, unit, better, fmt):
        out = [text(x0, mt - 10, title, 13, INK, weight="600"),
               text(x0 + panel_w, mt - 10, better, 11, MUTED, anchor="end")]
        vmax = max(obj[l][key] for l in OBJ_ORDER) * 1.15
        bar_h, step = 30, 56
        for i, lane in enumerate(OBJ_ORDER):
            v = obj[lane][key]
            y = mt + 14 + i * step
            bw = v / vmax * (panel_w - 200)
            hot = lane == "anvil-v2"
            out.append(text(x0, y + bar_h / 2 + 4, OBJ_LABEL[lane], 12,
                            INK if hot else INK2, weight="600" if hot else "normal"))
            out.append(f'<rect x="{x0 + 130}" y="{y}" width="{bw:.1f}" height="{bar_h}" '
                       f'rx="4" fill="{BLUE if hot else GRAY}"/>')
            out.append(text(x0 + 130 + bw + 8, y + bar_h / 2 + 4, fmt(v), 12,
                            INK if hot else INK2, weight="600" if hot else "normal"))
        return out

    s += panel(ml, "Maintainability Index (radon, avg)", "mi", "higher is better", "→ higher is better",
               lambda v: f"{v:.1f}")
    s += panel(ml + panel_w + gap, "Measured runtime (ms, avg)", "rt",
               "lower", "→ lower is better", lambda v: f"{v:.1f} ms")
    s.append(text(ml, h - 34, "Run cost for the same generations: Anvil "
                              f"{money(obj['anvil-v2']['cost'])} · gpt-5.6-luna "
                              f"{money(obj['gpt-5-6-luna']['cost'])} · opus-4.8 "
                              f"{money(obj['opus-4-8']['cost'])} · gpt-5.6-sol "
                              f"{money(obj['gpt-5-6-sol']['cost'])}", 12, INK2))
    s.append(text(w - 30, h - 12, "generated by assets/generate_charts.py from "
                                  "results/results-objective.json", 10, MUTED, anchor="end"))
    s.append("</svg>")
    return "\n".join(s) + "\n"


# ---------------------------------------------------------------- chart 3: gate lift
def chart_gate_lift(lanes):
    solo, gated = lanes["minimax-solo"], lanes["anvil-v2"]
    w, h = 920, 400
    ml, mt = 64, 96
    ph, pw = 220, 560
    ymax = 105.0
    s = svg_open(w, h, "Gate lift: the same cheap first-probe model scores 87.6 percent visible "
                       "and 83.8 percent hidden ungated; wrapped in the gate the pool reaches "
                       "100 percent visible and 98.4 percent hidden.")
    s.append(text(ml, 28, "The gate is the lift: same cheap pool, ungated vs. gated", 16, INK,
                  weight="600"))
    s.append(text(ml, 48, "minimax-solo is the gate-first executor's own first-probe model run "
                          "bare, one-shot. Anvil wraps the same cheap pool in the", 12, INK2))
    s.append(text(ml, 64, "visible machine gate with a non-regressive climb. Averages over the "
                          "same 5 tasks; the hidden gate is never shown to any builder.", 12, INK2))

    def Y(v):
        return mt + (ymax - v) / ymax * ph

    for v in (0, 25, 50, 75, 100):
        y = Y(v)
        s.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{ml + pw}" y2="{y:.1f}" '
                 f'stroke="{GRID}" stroke-width="1"/>')
        s.append(text(ml - 8, y + 4, str(v), 11, MUTED, anchor="end"))
    groups = [("visible gate % (133 checks)", solo["visible"], gated["visible"]),
              ("hidden gate % (63 checks)", solo["hidden"], gated["hidden"])]
    bw, inner = 96, 12
    for gi, (glabel, sv, gv) in enumerate(groups):
        gx = ml + 70 + gi * 280
        for (v, color, name) in ((sv, GRAY, "ungated"), (gv, BLUE, "gated")):
            x = gx if name == "ungated" else gx + bw + inner
            y = Y(v)
            s.append(f'<rect x="{x}" y="{y:.1f}" width="{bw}" '
                     f'height="{Y(0) - y:.1f}" rx="4" fill="{color}"/>')
            s.append(text(x + bw / 2, y - 8, f"{v:.1f}", 13,
                          INK if color == BLUE else INK2, anchor="middle",
                          weight="600" if color == BLUE else "normal"))
        s.append(text(gx + bw + inner / 2, Y(0) + 20, glabel, 12, INK2, anchor="middle"))
    # legend
    lx = ml + pw + 40
    for i, (color, label) in enumerate(((GRAY, "ungated: minimax-solo, one-shot"),
                                        (BLUE, "gated: Anvil, same pool + gate"))):
        y = mt + 20 + i * 26
        s.append(f'<rect x="{lx}" y="{y}" width="14" height="14" rx="3" fill="{color}"/>')
        s.append(text(lx + 22, y + 11, label, 11, INK2))
    s.append(text(lx, mt + 92, "Worst solo crack: expr_interp", 11, INK2))
    s.append(text(lx, mt + 108, "48% visible / 27% hidden.", 11, INK2))
    s.append(text(lx, mt + 124, "gated: 100% / 100%.", 11, INK2))
    s.append(text(lx, mt + 152, f"Cost, all 5 tasks: ungated", 11, MUTED))
    s.append(text(lx, mt + 168, f"{money(solo['cost_total'])} · gated "
                                f"{money(gated['cost_total'])}", 11, MUTED))
    s.append(text(w - 30, h - 12, "generated by assets/generate_charts.py from "
                                  "results/results-full.json", 10, MUTED, anchor="end"))
    s.append("</svg>")
    return "\n".join(s) + "\n"


# ---------------------------------------------------------------- main
def main():
    lanes = load_fold()
    check_against_shipped_table(lanes)
    obj = load_objective()
    os.makedirs(ASSETS, exist_ok=True)
    for name, svg in (("cost-vs-correctness.svg", chart_cost_vs_correctness(lanes)),
                      ("objective-substance.svg", chart_objective(obj)),
                      ("gate-lift.svg", chart_gate_lift(lanes))):
        path = os.path.join(ASSETS, name)
        with open(path, "w") as f:
            f.write(svg)
        print(f"wrote assets/{name}")
    # print the plotted numbers so a reader can spot-check against results/table.md
    print("\nplotted (chart 1): lane, avg cost/task, avg visible%")
    for lane in sorted(lanes):
        if lane in ("fable-5", "hermes"):
            continue
        L = lanes[lane]
        print(f"  {lane:18s} {L['cost_per_task']:.5f}  {L['visible']:5.1f}")


if __name__ == "__main__":
    main()
