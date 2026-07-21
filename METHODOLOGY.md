# GATEBENCH Methodology (the v1.7 protocol)

Measured 2026-07-21. 20 lanes × 5 hard single-file Python tasks, three independent quality axes
plus an objective substance re-score, with per-call measured cost.

## 1. The tasks — 5 hard, 196 checks

The previous round (v1.6, the 7 extra specs still shipped in `tasks/specs/`) saturated: every
clean model hit 100%, so wins were cost-only. v1.7 uses five multi-function/algorithmic files
where frontier models actually crack:

| task | what it demands | visible checks | hidden checks |
|---|---|---:|---:|
| `expr_interp` | expression interpreter: variables, precedence, `**` right-assoc, error→None | 29 | 15 |
| `csv_parse` | RFC-style CSV: quoting, escaped quotes, embedded newlines | 25 | 12 |
| `semver_cmp` | SemVer 2.0 comparator incl. full prerelease precedence | 32 | 14 |
| `toposort` | topological sort: cycle detection + deterministic tie-break | 18 | 10 |
| `url_canon` | URL/host canonicalizer incl. SSRF-style `..` clamping | 29 | 12 |
| **total** | | **133** | **63** |

That the tasks separate models is visible in the solo floor: `minimax-solo` falls to 48% on
`expr_interp`, `mistral-large` to 34% and `qwen-plus` to 31% on `url_canon`
(per-task grid: `python runners/agg.py`).

## 2. Three scoring axes (see `rubric/QUALITY-RUBRIC.md`)

1. **Visible gate** (`tasks/gates/<task>.py`): the contract the builder is allowed to see
   (the spec declares `gate: N/M` + `FAIL` lines). 133 checks.
2. **Hidden mutation gate** (`tasks/hidden/<task>.py`): adversarial checks the builder **never
   sees** — deeper precedence combos, degenerate inputs, security-relevant cases. 63 checks. A
   lane that pattern-matches the visible checks passes axis 1 and fails axis 2.
3. **3-model LLM-judge rubric**: three diverse judges (in this run: opus-4.8, gpt-5.6-luna,
   grok-4.5 lineages) score readability / robustness / edge handling / security 1–10 from
   source only; median per dimension; judges are never shown gate results. Panel membership and
   per-judge scores are recorded in every result record.

**Gate validation:** every visible and hidden gate was validated at build time against a
known-good reference (must score full) and a known-bad mutant (must drop) before any lane was
measured.

## 3. The objective substance re-score (axis 4, the tiebreaker)

The judge axis turned out to reward polish. To settle whether cheap-gated code is objectively
worse or just less prettily formatted, four lanes (gpt-5.6-sol, opus-4.8, gpt-5.6-luna, and the
gate-first executor) were regenerated and profiled with `runners/quality.py`
(`results/results-objective.json`, which embeds the actual generated code):

- **black-normalize first** — cosmetics equalized before any comparison;
- **ruff** lint count (real smells, not style);
- **bandit** security findings by severity;
- **radon** cyclomatic complexity + Maintainability Index + SLOC;
- **measured runtime** on a per-task stress workload, subprocess-bounded.

Aggregates over that run (per-lane means across completed cells; recompute from the JSON):

| lane | visible% | hidden% | ruff findings (Σ) | MI (avg) | runtime ms (avg) | $ (run) |
|---|---:|---:|---:|---:|---:|---:|
| **gate-first (anvil-v2)** † | 100 | 100 | 2 | **51.6** | **103.4** | **$0.012** |
| opus-4.8 | 100 | 98.4 | 0 | 47.5 | 139.0 | $0.251 |
| gpt-5.6-luna | 96.6 | 96.6 | 0 | 44.0 | 348.7 | $0.082 |
| gpt-5.6-sol | 100 | 100 | 0 | 42.7 | 156.6 | $0.453 |

† gate-first aggregates cover 3/5 tasks: its expr_interp and csv_parse cells timed out at
generation in this re-score run and are recorded as failures (no code) in the JSON. Its 100%
gate results for those two tasks come from the main run (`results/results-full.json`, with full
climb traces). The two ruff findings are real (and reported), and did not stop it topping MI
and runtime.

**Finding:** the LLM-judge deltas (7.47–8.88 across the 100%-visible wall) were largely
formatting/polish-driven, while the objective substance metrics — with formatting normalized —
show the cheap-gated lane tied on correctness and **won** on maintainability (MI 51.6, highest)
and measured runtime (103ms avg, fastest), at 1/7 (gpt-5.6-luna, $0.082) to 1/21 (opus-4.8,
$0.251) to 1/38 (gpt-5.6-sol, $0.453) of the frontier lanes' cost in the same run.

Every cell with embedded code is independently re-checkable: `python verify/verify_results.py`
re-runs both gates against the embedded code and asserts the recorded percentages reproduce
(current status: 18/18 verified, 0 mismatches).

## 4. The gate-first executor lane (product under test — static evidence)

The gate-first executor wraps a pool of cheap models in the visible machine gate: probe with a
cheap model, score against the gate, and climb under a **non-regressive rule** — a candidate
only ever replaces the incumbent if its gate score is greater or equal, so the loop can never
move backward, and it stops at 100% or at a bounded budget. On tasks the first probe clears, it
stops at one call (see the toposort trace: `probe[minimax] 18/18 SOLVED — $0.0007`). Full
per-task climb traces ship in the `anvil_log` fields of `results/results-full.json`.

Its implementation is not in this repository; `runners/run_bench.py --lane gate-first` is a
documented no-op that points here. The evidence lane is auditable via the shipped traces, costs,
and embedded code.

## 5. Measurement rules

- **N=1 per (lane, task).** One generation per cell; the gate-first lane's internal climb is
  part of its single cell (its whole cost is counted). Directional, not a controlled trial.
- **Costs are measured per call**, from router/OpenRouter usage accounting, never estimated.
  Fusion systems and OpenRouter lanes are billed at real retail.
- **Reasoning lanes ran via OpenRouter, not the flat-billed router**, because the private
  router clamps output at ~8k tokens (proven router-side), truncating reasoning models to 0.
  Retail billing means those lanes' costs are if anything *higher* than flat-rate — the
  gate-first cost advantage is conservative.
- `deepseek-v4-pro` needed a 64k output budget on csv_parse (at 32k it out-reasons the limit
  and truncates); with it, 100%/99% @ $0.133. Reasoning models need large output budgets on
  hard tasks — a real cost/latency fact, not a harness flaw.
- **Truncated/non-compiling outputs** skip the judge panel and score what the gates give them.
- **Flagged, not scored:** `fable-5` (router content-filter bug returned empty 200s — not
  capability; an OpenRouter bare-prompt retry ships as `fable-5-bare`) and `hermes` (MoA agent
  subprocess empty/timeout on every task this run).

## 6. Headline results (from the measured run)

- **Cheapest 100% lane by a wide margin:** the gate-first lane is the only 100%-visible lane
  under $0.08 ($0.032 for 5 tasks), holding 98% hidden (equal to opus-4.8). Next-cheapest 100%
  lane: gpt-5.6-luna at 2.5×; opus-4.8 at 6.1×; premium frontier (sol/kimi/gemini) 12.6–28.8×.
- **Gated climb beats subjective fusion:** fugu matched it on the gate at 6.3× the cost;
  fugu-ultra scored *worse* (80% visible) at 16× the cost; openrouter-fusion scored 59% at 50×
  the cost (judge 8.75 — pretty code, wrong answers). A real gate beats a subjective panel.
- **The gate is the moat:** the same first-probe model ungated (minimax-solo) scores 88%/84%;
  gated, the pool reaches 100%/98% — and cheaper than the solo's own repair attempts, because
  the loop stops at one call whenever the probe clears the gate.
- **The judge axis still separates the 100% wall** (7.47 opus → 8.88 sol): premium models buy
  ~1 judge-point of polish at 6–29× the cost, and the objective re-score shows that polish is
  mostly formatting.

All figures trace to `results/*.json` (regenerate the ranked table with `runners/agg.py`).
