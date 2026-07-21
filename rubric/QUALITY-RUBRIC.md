# v1.7 Quality Score — three independent axes

v1.6 scored only the visible gate (N/M). Every clean model hit 100% → no spread. v1.7 scores each
candidate on **three independent axes**, so models that all pass the visible gate still separate.

## Axis 1 — Visible gate (`gates/<task>.py`)
The gate the builder is allowed to see (it's in the spec's contract: `gate: N/M` + `FAIL` lines).
Correctness against the stated contract. **133 checks across 5 tasks.**

## Axis 2 — Hidden mutation gate (`hidden/<task>.py`)
Adversarial checks the builder **never sees** — extra edge cases, deeper precedence/precedence
combos, security-relevant inputs. A model that pattern-matches to the visible checks (or gets the
"happy path" right but misses the corners) passes Axis 1 and **fails Axis 2**. **63 checks.**
Emits `hidden: N/M`. Every hidden gate is validated to score full on the known-good reference and
to drop on a known-bad mutant (see the validation log in BENCHMARK-v1.7).

## Axis 3 — LLM-judge rubric (3-eye panel)
Beyond pass/fail: **is the code good?** Three diverse judge models score the candidate 1–10 on four
dimensions; we take the **median per dimension** (never trust one AI — the milestone-cadence
cross-audit principle applied to scoring). Judges see the spec + the candidate source, NOT the gate
results (so a judge can't anchor on the gate).

| Dimension | 1–10 asks |
|---|---|
| **Readability** | clear names, structure, no dead code, idiomatic Python |
| **Robustness** | handles malformed/adversarial input without crashing beyond what the gate tests |
| **Edge handling** | boundary conditions, empty/degenerate inputs, off-by-one correctness |
| **Security** | no eval/exec/compile, no injection surface, input validated, no silent-wrong fallbacks |

### Judge prompt (verbatim template)
```
You are one of three independent code reviewers scoring a candidate solution. Be strict and
calibrated: 5 = mediocre, 8 = solid production code, 10 = exemplary. Do NOT run the code; judge
from the source. You are NOT told whether it passes any test — score the code on its merits.

TASK SPEC:
<spec.md>

CANDIDATE SOURCE:
<candidate.py>

Score each dimension 1-10 and return ONLY compact JSON, no prose:
{"readability": N, "robustness": N, "edge": N, "security": N, "one_line": "<=12 word verdict"}
```

## Composite
Per (model, task): `visible_pct`, `hidden_pct`, `judge_median` (mean of the four medians), plus
`cost_usd` (measured). The headline table ranks by a blend but always shows all three axes + cost —
the point is to expose *where* a cheap solo cracks (usually Axis 2 first, then Axis 3), and whether
the gated lanes (anvil-v2 / flux-verified) hold quality-per-dollar as tasks get harder.

*Judges: 3 diverse lineages (e.g. opus-4.8, gpt-5.x, deepseek/grok) — picked at run time from the
key's allowed-models. Panel membership recorded in the results.*
