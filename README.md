# GATEBENCH

**A public, verifiable benchmark of the gate-first executor thesis:** wrap a pool of cheap models
in a machine gate and you match or beat frontier models on correctness — at a small fraction of
the cost — and you tie or win on *objective* code substance once formatting is normalized.

## The headline

On 5 hard single-file tasks (196 machine checks: 133 visible + 63 hidden a builder never sees),
the gate-first executor lane (`anvil-v2`) scored **100% visible / 98% hidden** — equal to or
better than every frontier lane — at **$0.032 for all 5 tasks**: the only 100%-visible lane under
$0.08. In the head-to-head objective re-score it cost **1/7th to 1/38th** of the frontier lanes
it was compared against ($0.012 vs $0.082–$0.452), and **won on objective substance**: highest
maintainability (**MI 51.6** vs 42.7–47.5) and fastest measured runtime (**103ms** avg vs
139–349ms), with formatting black-normalized before comparison.

Top of the 20-lane table, ranked by cost among lanes that hit 100% visible
(full table: [`results/table.md`](results/table.md), analysis: [`METHODOLOGY.md`](METHODOLOGY.md)):

| lane | via | visible% | hidden% | judge/10 | $ (5 tasks) | × vs gate-first |
|---|---|---:|---:|---:|---:|---:|
| **anvil-v2** (gate-first executor) | flux | **100** | **98** | **7.85** | **$0.032** | **1×** |
| gpt-5.6-luna | flux | 100 | 100 | 8.10 | $0.080 | 2.5× |
| deepseek-v4-pro | openrouter | 100 | 99 | 7.27 | $0.133 | 4.2× |
| opus-4.8 | flux | 100 | 98 | 7.47 | $0.194 | 6.1× |
| fugu (Sakana fusion) | system | 100 | 100 | 8.73 | $0.199 | 6.3× |
| gpt-5.6-terra | flux | 100 | 100 | 8.35 | $0.213 | 6.7× |
| gpt-5.6-sol | flux | 100 | 100 | 8.88 | $0.400 | 12.6× |
| claude-sonnet-5 | openrouter | 100 | 98 | 8.10 | $0.403 | 12.7× |
| kimi-k3 | openrouter | 100 | 100 | 8.82 | $0.872 | 27.5× |
| gemini-3.1-pro | openrouter | 100 | 100 | 7.90 | $0.915 | 28.8× |

The gate is the moat: `minimax-solo` — the gate-first executor's own first-probe model, run
*ungated* — scores 88% visible / 84% hidden (cracking to 48% on the expression interpreter).
Wrapped in the gate, the same cheap pool reaches 100% / 98%.

## What's in this repo

```
tasks/specs/     task specifications (the 5 v1.7 hard tasks + 7 earlier v1.6 tasks), verbatim
tasks/gates/     visible machine gates (pure stdlib, one per task) — the builder-facing contract
tasks/hidden/    hidden mutation gates (pure stdlib) — checks no builder ever saw
results/         every measurement JSON from the v1.7 run, verbatim (incl. embedded generated
                 code and the gate-first executor's full climb traces) + the ranked table
rubric/          the 3-model LLM-judge rubric (axis 3), verbatim
runners/         public OpenRouter runner, objective-quality profiler, table aggregator
verify/          verify_results.py (re-check shipped evidence) and leak_check.py (CI hygiene gate)
```

**The gate-first executor lane is the product under test — static evidence.** Its implementation
is not in this repository. Everything needed to *audit* its measured cells is: scores, per-call
costs, full climb traces (`anvil_log` in `results/results-full.json`), and the actual generated
code (`results/results-objective.json`), which you can re-score yourself, offline, in seconds.

## Reproduction quickstart

```bash
pip install -r requirements.txt        # black, radon, ruff, bandit (objective-quality tooling)

# 1. Verify the shipped evidence (no API key, no network — pure stdlib gate re-execution):
python verify/verify_results.py
#    Re-runs the visible + hidden gate for every embedded-code cell in results-objective.json
#    and asserts the recomputed percentages equal the recorded ones. Exits nonzero on mismatch.
#    Current status: 18/18 embedded-code cells verified, 0 mismatches.

# 2. Re-run the third-party-reproducible lanes yourself:
export OPENROUTER_API_KEY=...
python runners/run_bench.py --lane deepseek-v4-pro         # or kimi-k3, glm-5-2, claude-sonnet-5,
python runners/run_bench.py --lane vendor/any-model        # gemini-3-1-pro, or any raw slug
#    Writes results/results-local.json (never overwrites shipped evidence).

# 3. Objective substance profile of any candidate file:
python runners/quality.py my_solution.py url_canon

# 4. Regenerate the ranked table from the shipped JSONs:
python runners/agg.py                                      # writes results/table-regen.md

# 5. Repo hygiene gate (CI):
python verify/leak_check.py
```

## Honest limitations

- **Which lanes reproduce externally:** the five OpenRouter lanes (`deepseek-v4-pro`,
  `gemini-3-1-pro`, `claude-sonnet-5`, `kimi-k3`, `glm-5-2`) are directly re-runnable with
  `runners/run_bench.py` at real retail cost. Lanes marked `via flux` were measured through a
  private metered router using pinned aliases (see [`MODELS.md`](MODELS.md)); they map to public
  model families you can re-run through any provider, but the exact pinned snapshots are not
  re-runnable from here. Lanes marked `via system` (fugu, fugu-ultra, openrouter-fusion, hermes)
  are third-party fusion products invoked at measurement time. The gate-first lane itself is
  **static evidence** — audit it via `verify/verify_results.py` and the shipped traces.
- **N=1 per cell.** One generation per (lane, task). Directional, not a controlled trial.
- **The gate-first lane sees the visible gate during construction — by design.** That is its
  whole thesis. Solo lanes are one-shot and judged by the same gates. The *hidden* gate (which
  no lane ever sees) is the control for gate-overfitting: the gate-first lane holds 98% there.
- **Judge-panel caveats.** Axis 3 is a 3-model LLM judge (median per dimension). Its deltas
  tracked formatting/polish more than substance — that is exactly why the objective re-score
  (black-normalize, then ruff/bandit/radon/measured runtime) exists. Judges never see gate
  results, but LLM judges remain subjective instruments.
- **Objective-run coverage.** In the objective re-score, 2 of the gate-first lane's 20 cells
  (expr_interp, csv_parse) timed out at generation time and are recorded as failures with no
  code; its objective aggregates (MI 51.6, 103ms) cover the 3 completed tasks. Its 100%-gate
  results for those two tasks come from the main 20-lane run (with climb traces in
  `results/results-full.json`).
- **Two lanes are flagged, not scored as capability:** `fable-5` returned 0 due to a documented
  router content-filter bug (a bare-prompt OpenRouter retry, `fable-5-bare`, is included in
  `results/results-fable.json`), and `hermes` (MoA agent) returned empty/timeout on every task —
  a reliability observation about that product, not a graded score.

MIT licensed. See [`METHODOLOGY.md`](METHODOLOGY.md) for the full protocol and
[`MODELS.md`](MODELS.md) for the lane-to-model mapping.
