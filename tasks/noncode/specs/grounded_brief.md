# Task: grounded research brief (research/grounding, Tier-4 proof)

Write a research brief (18–35 sentences of prose; no headings, no lists) answering:
**"What did the 2026 gate-first executor benchmark establish, and what are its limits?"**

Use ONLY the sources below. Every sentence that states a fact MUST end with a citation marker
`[S1]`, `[S2]`, or `[S3]` (multiple markers allowed). Do not state any number that does not appear
in a source you cite for it. Do not cite a source for a fact it does not contain.

## Sources

**[S1]** The v1.7 benchmark evaluated 20 systems on 5 algorithmic tasks with 133 visible and 63
hidden checks. The gated cheap-model pool scored 100% on visible checks and 98% on hidden checks
at $0.032 average task cost, while the strongest frontier lane matched correctness at 6 to 29
times the cost. The same cheap pool without a gate scored 88% visible and 84% hidden.

**[S2]** An objective re-score normalized formatting with an auto-formatter, then measured lint
issues, security findings, cyclomatic complexity, maintainability index, and measured runtime.
The gated pool recorded the highest maintainability index (51.6) and the fastest runtime (103 ms)
in the fold, with zero high-severity security findings. LLM-judge preferences for frontier output
were driven mostly by formatting, not substance.

**[S3]** The benchmark's limits: tasks were single-file Python algorithms, so results may not
transfer to multi-file or non-code work. Gates were authored by the benchmark operators and
validated against reference solutions and known-bad mutants. A multi-round LLM polish stage was
tested and rejected because it reduced hidden-check correctness from 100% to 93% while raising
judge scores. The verification gates are not tamper-proof against adversarial submissions.
