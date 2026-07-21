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
  cost-per-correct-task.svg horizontal bars: only the lanes that scored 100% visible,
                            sorted by measured avg cost per task, with the cost
                            multiple vs Anvil on every bar.
  four-ways-to-spend.svg    the category slice: gated pool / frontier solo /
                            fusion systems / low-cost solo, avg visible % and avg cost
                            per task per group, computed from the same fold.
  gated-vs-fusion.svg       the multi-model head-to-head: Anvil vs fugu, fugu-ultra,
                            openrouter-fusion; visible and hidden gate % with cost
                            per task and the multiple vs Anvil under each system.
  hero.svg                  the dark 1200x630 share graphic: the ten lanes at 100%
                            visible in two mirrored panels, correctness parity on the
                            left, measured cost per task (linear, heat-colored by the
                            multiple vs the gated pool) on the right, lowest cost first
                            so the gated pool is the top row.
  hero-quality.svg          the dark 1200x630 quality card: the 4 objectively profiled
                            lanes (results-objective.json) across three panels, namely
                            maintainability index, measured runtime, and run cost, with
                            the gated pool as the top row of each panel.
  gated-climb-flow.svg      static hand-laid flow diagram of the gated-climb method
                            (probe, gate, targeted repair, escalate, honest stop); no
                            benchmark data, light theme like the non-hero charts.

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
            "ok_n": len(ok),
            "n": len(rs),
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
    s = svg_open(w, h, "Gate lift: the same first-probe model scores 87.6 percent visible "
                       "and 83.8 percent hidden ungated; wrapped in the gate the pool reaches "
                       "100 percent visible and 98.4 percent hidden.")
    s.append(text(ml, 28, "The gate is the lift: same pool, ungated vs. gated", 16, INK,
                  weight="600"))
    s.append(text(ml, 48, "minimax-solo is the gate-first executor's own first-probe model run "
                          "bare, one-shot. Anvil wraps the same pool of models in the", 12, INK2))
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


# ---------------------------------------------------------------- chart 4: cost per correct task
def perfect_lanes(lanes):
    """Lanes at exactly 100% average visible, cheapest first."""
    return sorted((l for l in lanes if lanes[l]["visible"] >= 100.0 - 1e-9),
                  key=lambda l: lanes[l]["cost_per_task"])


def chart_cost_per_correct(lanes):
    order = perfect_lanes(lanes)
    base = lanes["anvil-v2"]["cost_per_task"]
    n = len(order)
    w = 920
    mt, step, bar_h = 108, 38, 24
    label_x, bar_x0, bar_w = 196, 208, 470
    h = mt + n * step + 66
    xmax = max(lanes[l]["cost_per_task"] for l in order)
    s = svg_open(w, h, f"Horizontal bars: measured average cost per task for the {n} "
                       f"lanes that scored 100 percent on the visible gate; Anvil is "
                       f"cheapest at {money(base)} per task.")
    s.append(text(40, 28, f"The price of a correct task: {n} systems at 100%, one at "
                          f"{money(base)}", 16, INK, weight="600"))
    s.append(text(40, 48, f"Every lane below cleared all 133 visible checks across the same "
                          f"5 tasks. Bars are measured avg cost per task (5-task total / 5),", 12, INK2))
    s.append(text(40, 64, "cheapest first, with the cost multiple vs the gated pool. "
                          "Same fold as the full 20-lane table.", 12, INK2))
    # vertical gridlines
    for c in (0.05, 0.10, 0.15):
        x = bar_x0 + c / xmax * bar_w
        s.append(f'<line x1="{x:.1f}" y1="{mt - 8}" x2="{x:.1f}" y2="{mt + n * step - 8}" '
                 f'stroke="{GRID}" stroke-width="1"/>')
        s.append(text(x, mt + n * step + 8, f"${c:.2f}", 11, MUTED, anchor="middle"))
    for i, lane in enumerate(order):
        L = lanes[lane]
        y = mt + i * step
        hot = lane == "anvil-v2"
        disp = "Anvil" if hot else lane
        bw = max(L["cost_per_task"] / xmax * bar_w, 2.0)
        s.append(text(label_x, y + bar_h / 2 + 4, disp, 12, INK if hot else INK2,
                      anchor="end", weight="600" if hot else "normal"))
        s.append(f'<rect x="{bar_x0}" y="{y}" width="{bw:.1f}" height="{bar_h}" '
                 f'rx="4" fill="{BLUE if hot else GRAY}"/>')
        mult = "baseline" if hot else f"{L['cost_per_task'] / base:.1f}x"
        s.append(text(bar_x0 + bw + 8, y + bar_h / 2 + 4,
                      f"${L['cost_per_task']:.4f} · {mult}", 12,
                      INK if hot else INK2, weight="600" if hot else "normal"))
    s.append(text(bar_x0 + bar_w / 2, mt + n * step + 28,
                  "measured avg cost per task (USD)", 12, INK2, anchor="middle"))
    s.append(text(w - 30, h - 12, "generated by assets/generate_charts.py from "
                                  "results/results-full.json + results-pass2.json",
                  10, MUTED, anchor="end"))
    s.append("</svg>")
    return "\n".join(s) + "\n"


# ---------------------------------------------------------------- chart 5: four ways to spend
GROUPS = [
    ("Gated pool (Anvil)", ["anvil-v2"]),
    ("Frontier solo", ["gpt-5-6-sol", "gpt-5-6-terra", "gpt-5-6-luna", "gemini-3-1-pro",
                       "opus-4-8", "claude-sonnet-5", "kimi-k3", "grok-4-5",
                       "deepseek-v4-pro"]),
    ("Fusion systems", ["fugu", "fugu-ultra", "openrouter-fusion"]),
    ("Solo, low-cost tier", ["minimax-solo", "mistral-large", "qwen-plus", "claude-haiku"]),
]


def group_stats(lanes):
    out = []
    for name, members in GROUPS:
        vis = sum(lanes[m]["visible"] for m in members) / len(members)
        cpt = sum(lanes[m]["cost_per_task"] for m in members) / len(members)
        out.append((name, len(members), vis, cpt))
    return out


def chart_four_ways(lanes):
    stats = group_stats(lanes)
    w, h = 920, 404
    panel_w, gap, ml, mt = 400, 60, 40, 112
    step, bar_h = 66, 24
    s = svg_open(w, h, "Two panels: average visible-gate percentage and average measured "
                       "cost per task for four approach groups: gated pool, frontier "
                       "solo, fusion systems, low-cost solo.")
    s.append(text(ml, 28, "Four ways to spend: same tasks, same checks", 16, INK, weight="600"))
    s.append(text(ml, 48, "The 20-lane fold grouped by approach: averages per group over the "
                          "same 5 tasks and 133 visible checks. The gated pool", 12, INK2))
    s.append(text(ml, 64, "is the only group that pairs a 100% visible average with a "
                          "sub-cent cost per task.", 12, INK2))
    s.append(text(ml, 80, "Outside these four groups: glm-5-2 (ungrouped) and the two flagged "
                          "lanes, fable-5 and hermes (not capability scores).", 11, MUTED))

    def panel(x0, title, val, fmt, vmax):
        out = [text(x0, mt - 10, title, 13, INK, weight="600")]
        for i, (name, cnt, vis, cpt) in enumerate(stats):
            v = val(vis, cpt)
            y = mt + 8 + i * step
            hot = i == 0
            lab = f"{name} · {cnt} lane" + ("s" if cnt > 1 else "")
            out.append(text(x0, y, lab, 12, INK if hot else INK2,
                            weight="600" if hot else "normal"))
            bw = max(v / vmax * (panel_w - 80), 2.0)
            out.append(f'<rect x="{x0}" y="{y + 8}" width="{bw:.1f}" height="{bar_h}" '
                       f'rx="4" fill="{BLUE if hot else GRAY}"/>')
            out.append(text(x0 + bw + 8, y + 8 + bar_h / 2 + 4, fmt(v), 12,
                            INK if hot else INK2, weight="600" if hot else "normal"))
        return out

    s += panel(ml, "avg visible-gate % (higher is better)",
               lambda vis, cpt: vis, lambda v: f"{v:.1f}%", 105.0)
    s += panel(ml + panel_w + gap, "avg cost per task, USD (lower is better)",
               lambda vis, cpt: cpt,
               lambda v: f"${v:.4f}", max(g[3] for g in stats) * 1.12)
    s.append(text(w - 30, h - 12, "generated by assets/generate_charts.py from "
                                  "results/results-full.json + results-pass2.json",
                  10, MUTED, anchor="end"))
    s.append("</svg>")
    return "\n".join(s) + "\n"


# ---------------------------------------------------------------- chart 6: gated vs fusion
RIVALS = ["anvil-v2", "fugu", "fugu-ultra", "openrouter-fusion"]


def chart_gated_vs_fusion(lanes):
    base = lanes["anvil-v2"]["cost_per_task"]
    w, h = 920, 500
    ml, mt, ph = 64, 112, 230
    ymax = 105.0
    s = svg_open(w, h, "Grouped bars: visible and hidden gate percentages for the four "
                       "multi-model systems; Anvil holds 100 percent visible at "
                       f"{money(base)} per task while the fusion systems cost "
                       f"{lanes['fugu']['cost_per_task'] / base:.1f}x to "
                       f"{lanes['openrouter-fusion']['cost_per_task'] / base:.1f}x as much.")
    s.append(text(ml, 28, "Multi-model vs multi-model: the gate is the difference", 16, INK,
                  weight="600"))
    s.append(text(ml, 48, "Four systems that combine multiple models on the same 5 tasks: "
                          "three fusion/ensemble products vs the gated-pool", 12, INK2))
    s.append(text(ml, 64, "climb (Anvil). Fusion merges opinions; the gate verifies output "
                          "against the visible machine contract and climbs until it passes.", 12, INK2))

    def Y(v):
        return mt + (ymax - v) / ymax * ph

    for v in (0, 25, 50, 75, 100):
        y = Y(v)
        s.append(f'<line x1="{ml}" y1="{y:.1f}" x2="{ml + 780}" y2="{y:.1f}" '
                 f'stroke="{GRID}" stroke-width="1"/>')
        s.append(text(ml - 8, y + 4, str(v), 11, MUTED, anchor="end"))
    bw, inner = 64, 10
    for gi, lane in enumerate(RIVALS):
        L = lanes[lane]
        hot = lane == "anvil-v2"
        color = BLUE if hot else GRAY
        gx = ml + 56 + gi * 190
        for j, v in enumerate((L["visible"], L["hidden"])):
            x = gx + j * (bw + inner)
            y = Y(v)
            op = "" if j == 0 else ' fill-opacity="0.5"'
            s.append(f'<rect x="{x}" y="{y:.1f}" width="{bw}" '
                     f'height="{Y(0) - y:.1f}" rx="4" fill="{color}"{op}/>')
            s.append(text(x + bw / 2, y - 8, f"{v:.1f}", 12,
                          INK if hot else INK2, anchor="middle",
                          weight="600" if hot else "normal"))
        cx = gx + bw + inner / 2
        disp = "Anvil" if hot else lane
        s.append(text(cx, Y(0) + 20, disp, 13, INK if hot else INK2, anchor="middle",
                      weight="600" if hot else "normal"))
        mult = "baseline" if hot else f"{L['cost_per_task'] / base:.1f}x vs Anvil"
        s.append(text(cx, Y(0) + 38, f"${L['cost_per_task']:.4f}/task · {mult}", 11,
                      INK if hot else MUTED, anchor="middle",
                      weight="600" if hot else "normal"))
    # legend
    lx = ml + 56
    s.append(f'<rect x="{lx}" y="{mt - 26}" width="14" height="14" rx="3" fill="{INK2}"/>')
    s.append(text(lx + 22, mt - 15, "visible gate % (133 checks)", 11, INK2))
    s.append(f'<rect x="{lx + 210}" y="{mt - 26}" width="14" height="14" rx="3" '
             f'fill="{INK2}" fill-opacity="0.5"/>')
    s.append(text(lx + 232, mt - 15, "hidden gate % (63 checks, never shown to any builder)",
                  11, INK2))
    s.append(text(ml, h - 34, "hermes (MoA agent): empty output on every task, flagged, "
                              "not plotted.", 11, MUTED))
    s.append(text(w - 30, h - 12, "generated by assets/generate_charts.py from "
                                  "results/results-full.json + results-pass2.json",
                  10, MUTED, anchor="end"))
    s.append("</svg>")
    return "\n".join(s) + "\n"


# ---------------------------------------------------------------- chart 7: hero (dark share graphic)
# dark palette, hero cards only
SURFACE_D = "#0e1113"
INK_D = "#e8eaec"
INK2_D = "#a6adb3"
GRID_D = "#2c3237"
STEEL_D = "#3e5a75"   # correctness bars and non-highlighted quality bars
GREEN_D = "#2fbf5f"   # the gated pool
AMBER_D = "#d9a441"   # cost heat: low multiples vs the gated pool
RED_D = "#d96a4a"     # cost heat: double-digit multiples vs the gated pool


def heat(mult):
    """Cost-bar heat color by multiple vs the gated pool baseline."""
    return GREEN_D if mult <= 1.0 else RED_D if mult >= 12.0 else AMBER_D


def hero_order(lanes):
    """The 100%-visible lanes, lowest cost per task first (gated pool on top)."""
    return perfect_lanes(lanes)


def chart_hero(lanes):
    order = hero_order(lanes)
    n = len(order)
    base = lanes["anvil-v2"]["cost_per_task"]
    xmax = max(lanes[l]["cost_per_task"] for l in order)
    w, h = 1200, 630
    y0, step, bar_h = 140, 40, 26
    lw = 360                    # bar track width, both panels
    lx1, rx0 = 515, 685         # left-panel bars end at lx1; right-panel bars start at rx0
    rows_top = y0 - 8
    rows_bot = y0 + (n - 1) * step + bar_h + 8
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
         f'viewBox="0 0 {w} {h}" role="img" aria-label="Dual-panel dark chart: the {n} '
         'lanes that scored 100 percent on the visible gate, sorted by measured cost per '
         'task. Left panel: correctness, all tied at 100 percent. Right panel: cost per '
         f'task on a linear scale, from ${base:.4f} for Anvil on the top row down to '
         f'${xmax:.4f} at the bottom, a {xmax / base:.1f}x spread.">',
         f'<rect width="{w}" height="{h}" fill="{SURFACE_D}"/>']
    s.append(text(60, 48, f"{n} systems scored 100%. Here's what each one paid.",
                  23, INK_D, weight="700"))
    s.append(text(60, 74, f"{len(TASKS)} tasks, 133 visible machine checks, measured "
                          "spend per task. Fold run, every lane 5/5 tasks completed.",
                  13, INK2_D))
    s.append(text(lx1 - lw / 2, 118, "correctness: all tied at 100%", 13, INK_D,
                  anchor="middle", weight="600"))
    s.append(text(rx0 + lw / 2, 118, "measured cost per task (USD)", 13, INK_D,
                  anchor="middle", weight="600"))
    # gridlines behind the bars: mirrored % ticks on the left, linear USD ticks on the right
    for v in (25, 50, 75, 100):
        x = lx1 - v / 100 * lw
        s.append(f'<line x1="{x:.1f}" y1="{rows_top}" x2="{x:.1f}" y2="{rows_bot}" '
                 f'stroke="{GRID_D}" stroke-width="1"/>')
    for v in (0, 50, 100):
        s.append(text(lx1 - v / 100 * lw, rows_bot + 18, str(v), 11, INK2_D,
                      anchor="middle"))
    for c in (0.05, 0.10, 0.15):
        x = rx0 + c / xmax * lw
        s.append(f'<line x1="{x:.1f}" y1="{rows_top}" x2="{x:.1f}" y2="{rows_bot}" '
                 f'stroke="{GRID_D}" stroke-width="1"/>')
        s.append(text(x, rows_bot + 18, f"${c:.2f}", 11, INK2_D, anchor="middle"))
    for i, lane in enumerate(order):
        L = lanes[lane]
        y = y0 + i * step
        hot = lane == "anvil-v2"
        m = L["cost_per_task"] / base
        wt = "700" if hot else "normal"
        disp = "Anvil" if hot else lane
        bw = max(L["cost_per_task"] / xmax * lw, 2.0)
        if hot:
            # subtle glow behind the highlighted bars
            s.append(f'<rect x="{lx1 - lw - 3:.1f}" y="{y - 3}" width="{lw + 6}" '
                     f'height="{bar_h + 6}" rx="7" fill="{GREEN_D}" fill-opacity="0.28"/>')
            s.append(f'<rect x="{rx0 - 3}" y="{y - 3}" width="{bw + 6:.1f}" '
                     f'height="{bar_h + 6}" rx="7" fill="{GREEN_D}" fill-opacity="0.28"/>')
        s.append(f'<rect x="{lx1 - lw}" y="{y}" width="{lw}" height="{bar_h}" '
                 f'rx="4" fill="{GREEN_D if hot else STEEL_D}"/>')
        s.append(text(lx1 - lw - 10, y + bar_h / 2 + 4, "100", 12, INK_D, anchor="end",
                      weight=wt))
        s.append(text((lx1 + rx0) / 2, y + bar_h / 2 + 4, disp, 13,
                      INK_D if hot else INK2_D, anchor="middle", weight=wt))
        s.append(f'<rect x="{rx0}" y="{y}" width="{bw:.1f}" height="{bar_h}" '
                 f'rx="4" fill="{heat(m)}"/>')
        mult = "baseline" if hot else f"{m:.1f}x"
        s.append(text(rx0 + bw + 10, y + bar_h / 2 + 4,
                      f"${L['cost_per_task']:.4f} · {mult}", 12, INK_D, weight=wt))
    s.append(text(lx1 - lw / 2, rows_bot + 44, "avg visible-gate % (133 checks per lane)",
                  11, INK2_D, anchor="middle"))
    s.append(text(rx0 + lw / 2, rows_bot + 44, "linear scale; multiple vs Anvil on each bar",
                  11, INK2_D, anchor="middle"))
    s.append(text(60, h - 14, "github.com/FerroxLabs/gatebench", 10, INK2_D))
    s.append(text(w - 60, h - 14, "generated by assets/generate_charts.py from "
                                  "results/results-full.json + results-pass2.json",
                  10, INK2_D, anchor="end"))
    s.append("</svg>")
    return "\n".join(s) + "\n"


# ---------------------------------------------------------------- chart 8: hero quality card (dark)
Q_ORDER = ["anvil-v2", "opus-4-8", "gpt-5-6-sol", "gpt-5-6-luna"]


def chart_hero_quality(obj):
    w, h = 1200, 630
    x0s, pw = (60, 450, 840), 340
    y0, step, bar_h = 192, 90, 42
    label_w, track = 100, 150
    A = obj["anvil-v2"]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
         f'viewBox="0 0 {w} {h}" role="img" aria-label="Three-panel dark chart over the '
         '4 objectively profiled lanes. Anvil, the top row of every panel, has the '
         f'highest maintainability index at {A["mi"]:.1f}, the fastest measured runtime '
         f'at {A["rt"]:.0f} ms, and the lowest run cost at ${A["cost"]:.3f}.">',
         f'<rect width="{w}" height="{h}" fill="{SURFACE_D}"/>']
    s.append(text(60, 48, "Better code. Faster code. A fraction of the bill.",
                  23, INK_D, weight="700"))
    s.append(text(60, 74, "4 leading lanes, formatting normalized before scoring; all 4 "
                          "at 100% visible correctness. Objective re-score run; Anvil "
                          "aggregates cover the", 13, INK2_D))
    s.append(text(60, 94, f"{A['ok_n']} of {A['n']} tasks that completed generation, "
                          "timeouts disclosed in the repo.", 13, INK2_D))

    def panel(x0, title, key, fmt):
        out = [text(x0, 156, title, 13, INK_D, weight="600")]
        vmax = max(obj[l][key] for l in Q_ORDER) * 1.12
        for i, lane in enumerate(Q_ORDER):
            v = obj[lane][key]
            y = y0 + i * step
            hot = lane == "anvil-v2"
            wt = "700" if hot else "normal"
            disp = "Anvil" if hot else lane
            bw = max(v / vmax * track, 2.0)
            out.append(text(x0 + label_w, y + bar_h / 2 + 4, disp, 12,
                            INK_D if hot else INK2_D, anchor="end", weight=wt))
            out.append(f'<rect x="{x0 + label_w + 12}" y="{y}" width="{bw:.1f}" '
                       f'height="{bar_h}" rx="4" fill="{GREEN_D if hot else STEEL_D}"/>')
            out.append(text(x0 + label_w + 12 + bw + 8, y + bar_h / 2 + 4, fmt(v), 12,
                            INK_D, weight=wt))
        return out

    s += panel(x0s[0], "maintainability index (higher is better)", "mi",
               lambda v: f"{v:.1f}")
    s += panel(x0s[1], "measured runtime ms (lower is better)", "rt",
               lambda v: f"{v:.0f} ms")
    s += panel(x0s[2], "run cost USD (lower is better)", "cost",
               lambda v: f"${v:.3f}")
    s.append(text(60, h - 14, "github.com/FerroxLabs/gatebench", 10, INK2_D))
    s.append(text(w - 60, h - 14, "generated by assets/generate_charts.py from "
                                  "results/results-objective.json", 10, INK2_D,
                  anchor="end"))
    s.append("</svg>")
    return "\n".join(s) + "\n"


# ---------------------------------------------------------------- chart 9: gated-climb flow diagram
# Static hand-laid method diagram: light theme, no benchmark data. Every coordinate is a
# literal, so the output is trivially deterministic.
FLOW_GREEN = "#2f9e44"
FLOW_RED = "#c8553d"
NODE_STROKE = AXIS
NODE_FILL = "#ffffff"
DIA_FILL = "#f4f3ec"


def chart_flow():
    w, h = 920, 760
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
         f'viewBox="0 0 {w} {h}" role="img" aria-label="Flow diagram of the gated climb: '
         'probe with one low-cost model, run the visible gate, exit on green after a free '
         'tooling polish, otherwise loop: pick the first failing check, repair with an '
         'untried low-cost model or escalate up the ladder, re-gate, keep only strict '
         'improvements, and stop honestly when the budget is spent or the climb plateaus.">',
         f'<rect width="{w}" height="{h}" fill="{SURFACE}"/>',
         '<defs>']
    for mid, color in (("ah", INK2), ("ahg", FLOW_GREEN), ("ahr", FLOW_RED), ("ahb", BLUE)):
        s.append(f'<marker id="{mid}" markerWidth="9" markerHeight="8" refX="7.5" '
                 f'refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="{color}"/>'
                 '</marker>')
    s.append('</defs>')

    def node(x, y, bw, bh, lines, color=INK, weight="normal", fill=NODE_FILL,
             stroke=NODE_STROKE, size=12):
        out = [f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="8" '
               f'fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>']
        cy = y + bh / 2 - (len(lines) - 1) * 9 + 4
        for ln in lines:
            out.append(text(x + bw / 2, cy, ln, size, color, anchor="middle",
                            weight=weight))
            cy += 18
        return out

    def dia(cx, cy, rx, ry, label, size=11):
        return [f'<polygon points="{cx - rx},{cy} {cx},{cy - ry} {cx + rx},{cy} '
                f'{cx},{cy + ry}" fill="{DIA_FILL}" stroke="{NODE_STROKE}" '
                'stroke-width="1.2"/>',
                text(cx, cy + 4, label, size, INK, anchor="middle", weight="600")]

    def edge(d, color=INK2, marker="ah"):
        return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6" '
                f'marker-end="url(#{marker})"/>')

    s.append(text(40, 32, "The gated climb: how one task moves through the executor",
                  16, INK, weight="600"))
    # top spine
    s += node(40, 64, 165, 36, ["task + gate script"])
    s.append(edge("M205,82 L241,82"))
    s += node(245, 64, 235, 36, ["PROBE: 1 low-cost model, 1 attempt"])
    s.append(edge("M480,82 L516,82"))
    s += node(520, 64, 115, 36, ["RUN GATE"], color=BLUE, weight="600")
    s.append(edge("M635,82 L676,82"))
    s += dia(745, 82, 65, 26, "green?", size=12)
    # happy exit: green -> free polish -> DONE
    s.append(edge("M810,82 L850,82 Q860,82 860,92 L860,110 Q860,120 850,120 "
                  "L800,120 Q790,120 790,130 L790,142", FLOW_GREEN, "ahg"))
    s.append(text(868, 106, "yes", 11, FLOW_GREEN, weight="600"))
    s += node(600, 146, 210, 36, ["free tooling polish, re-gate"])
    s.append(edge("M810,164 L826,164", FLOW_GREEN, "ahg"))
    s += node(830, 146, 80, 36, ["DONE"], color=FLOW_GREEN, weight="700",
              fill="#e9f5ec", stroke=FLOW_GREEN)
    s.append(text(755, 202, "most easy tasks end here: $0.0007", 11, MUTED,
                  anchor="middle"))
    # red exit: not green -> pick target
    s.append(edge("M745,108 L745,122 Q745,132 735,132 L310,132 Q300,132 300,142 "
                  "L300,176", FLOW_RED, "ahr"))
    s.append(text(755, 126, "no", 11, FLOW_RED, weight="600"))
    s += node(140, 180, 320, 48, ["pick target: first failing check",
                                  "with an untried model"])
    s.append(edge("M300,228 L300,246"))
    s += dia(300, 284, 125, 34, "untried low-cost model?")
    # repair vs escalate
    s.append(edge("M300,318 L300,348", FLOW_GREEN, "ahg"))
    s.append(text(308, 338, "yes", 11, FLOW_GREEN, weight="600"))
    s += node(120, 352, 330, 48, ["surgical repair: spec + candidate",
                                  "+ check NAMES only"])
    s.append(edge("M425,284 L466,284"))
    s.append(text(432, 276, "no", 11, INK2, weight="600"))
    s += node(470, 266, 225, 36, ["ESCALATE up the model ladder"])
    s.append(text(612, 330, "the only place a frontier model gets called", 11, MUTED))
    # both feed the gate
    s.append(edge("M250,400 L250,432"))
    s.append(edge("M582,302 L582,444 Q582,454 572,454 L481,454"))
    s += node(237, 436, 240, 36, ["RUN GATE on candidate"], color=BLUE, weight="600")
    s.append(edge("M357,472 L357,500"))
    s += dia(357, 538, 105, 34, "better?", size=12)
    s.append(text(357, 598, "better = score strictly up, or a tie with strictly fewer "
                            "failures", 11, MUTED, anchor="middle"))
    # accept / discard
    s.append(edge("M462,538 L518,538", FLOW_GREEN, "ahg"))
    s.append(text(472, 530, "yes", 11, FLOW_GREEN, weight="600"))
    s += node(522, 520, 180, 36, ["accept: new best"])
    s.append(edge("M252,538 L226,538", FLOW_RED, "ahr"))
    s.append(text(237, 530, "no", 11, FLOW_RED, weight="600"))
    s += node(40, 514, 182, 48, ["discard, remember model", "failed this check"])
    # the climb: both outcomes rejoin the loop, with a budget/plateau side exit
    s.append(f'<path d="M612,556 L612,624" fill="none" stroke="{BLUE}" '
             'stroke-width="1.6"/>')
    s.append(edge("M131,562 L131,614 Q131,624 141,624 L640,624", BLUE, "ahb"))
    s += dia(760, 624, 115, 30, "budget spent or plateau?")
    s.append(edge("M875,624 L888,624 Q898,624 898,614 L898,232 Q898,222 888,222 "
                  "L466,222", BLUE, "ahb"))
    s.append(f'<text x="884" y="430" {FONT} font-size="12" fill="{BLUE}" '
             'text-anchor="middle" font-weight="600" '
             'transform="rotate(-90 884 430)">the climb</text>')
    s.append(edge("M760,654 L760,668", FLOW_GREEN, "ahg"))
    s.append(text(768, 666, "yes", 11, FLOW_GREEN, weight="600"))
    s += node(596, 672, 310, 40, ["STOP: return best so far, report honestly"],
              weight="600")
    s.append(text(751, 732, "no fake green, no infinite loop", 11, MUTED,
                  anchor="middle"))
    s.append(text(w - 30, h - 10, "generated by assets/generate_charts.py "
                                  "(static method diagram, no data plotted)",
                  10, MUTED, anchor="end"))
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
                      ("gate-lift.svg", chart_gate_lift(lanes)),
                      ("cost-per-correct-task.svg", chart_cost_per_correct(lanes)),
                      ("four-ways-to-spend.svg", chart_four_ways(lanes)),
                      ("gated-vs-fusion.svg", chart_gated_vs_fusion(lanes)),
                      ("hero.svg", chart_hero(lanes)),
                      ("hero-quality.svg", chart_hero_quality(obj)),
                      ("gated-climb-flow.svg", chart_flow())):
        path = os.path.join(ASSETS, name)
        with open(path, "w") as f:
            f.write(svg)
        print(f"wrote assets/{name}")
    # print the plotted numbers so a reader can spot-check against results/table.md
    print("\nplotted (cost-vs-correctness): lane, avg cost/task, avg visible%")
    for lane in sorted(lanes):
        if lane in ("fable-5", "hermes"):
            continue
        L = lanes[lane]
        print(f"  {lane:18s} {L['cost_per_task']:.5f}  {L['visible']:5.1f}")
    base = lanes["anvil-v2"]["cost_per_task"]
    print("\nplotted (cost-per-correct-task): 100%-visible lanes, cheapest first")
    for lane in perfect_lanes(lanes):
        L = lanes[lane]
        mult = "baseline" if lane == "anvil-v2" else f"{L['cost_per_task'] / base:.1f}x"
        print(f"  {lane:18s} ${L['cost_per_task']:.4f}/task  {mult}")
    print("\nplotted (four-ways-to-spend): group, lanes, avg visible%, avg cost/task")
    for name, cnt, vis, cpt in group_stats(lanes):
        print(f"  {name:26s} n={cnt}  {vis:5.1f}%  ${cpt:.4f}")
    print("\nplotted (gated-vs-fusion): system, visible%, hidden%, cost/task, x vs Anvil")
    for lane in RIVALS:
        L = lanes[lane]
        mult = "baseline" if lane == "anvil-v2" else f"{L['cost_per_task'] / base:.1f}x"
        print(f"  {lane:18s} {L['visible']:5.1f}  {L['hidden']:5.1f}  "
              f"${L['cost_per_task']:.4f}  {mult}")
    print("\nplotted (hero): 100%-visible lanes, lowest cost per task first")
    for lane in hero_order(lanes):
        L = lanes[lane]
        mult = "baseline" if lane == "anvil-v2" else f"{L['cost_per_task'] / base:.1f}x"
        print(f"  {lane:18s} visible {L['visible']:5.1f}  ${L['cost_per_task']:.4f}/task  {mult}")
    print("\nplotted (hero-quality): lane, completed cells, MI, runtime ms, run cost")
    for lane in Q_ORDER:
        O = obj[lane]
        print(f"  {lane:14s} {O['cells']}  mi {O['mi']:.1f}  rt {O['rt']:.0f} ms  "
              f"${O['cost']:.3f}")
    print("\ngated-climb-flow.svg: static method diagram, no data plotted")


if __name__ == "__main__":
    main()
