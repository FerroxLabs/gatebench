#!/usr/bin/env python3
"""Tier-4 (Grounding) gate for the grounded_brief proof task — deterministic grounding proxy.
Checks citation discipline + number-level grounding: every number stated must appear in a source
the sentence cites; every factual sentence must carry a valid citation. The production path uses
model-based NLI entailment (judge != generator); this gate is the deterministic, reproducible
subset suitable for offline proof runs. Orchestrator-authored; stdlib only; fail-closed.
Usage: grounded_brief.py <artifact.md|txt>"""
import re, sys

SOURCES = {
    "S1": "The v1.7 benchmark evaluated 20 systems on 5 algorithmic tasks with 133 visible and 63 "
          "hidden checks. The gated cheap-model pool scored 100% on visible checks and 98% on hidden "
          "checks at $0.032 average task cost, while the strongest frontier lane matched correctness "
          "at 6 to 29 times the cost. The same cheap pool without a gate scored 88% visible and 84% hidden.",
    "S2": "An objective re-score normalized formatting with an auto-formatter, then measured lint "
          "issues, security findings, cyclomatic complexity, maintainability index, and measured runtime. "
          "The gated pool recorded the highest maintainability index (51.6) and the fastest runtime (103 ms) "
          "in the fold, with zero high-severity security findings. LLM-judge preferences for frontier "
          "output were driven mostly by formatting, not substance.",
    "S3": "The benchmark's limits: tasks were single-file Python algorithms, so results may not "
          "transfer to multi-file or non-code work. Gates were authored by the benchmark operators and "
          "validated against reference solutions and known-bad mutants. A multi-round LLM polish stage "
          "was tested and rejected because it reduced hidden-check correctness from 100% to 93% while "
          "raising judge scores. The verification gates are not tamper-proof against adversarial submissions.",
}
_NUM = re.compile(r"\d+(?:\.\d+)?")
_CIT = re.compile(r"\[(S\d+)\]")

def nums(text):
    return set(_NUM.findall(text))

def main(path):
    text = open(path, "r", encoding="utf-8").read().strip()
    text = re.sub(r"^```.*?\n|\n```$", "", text, flags=re.S)
    # sentence split: on ., !, ? followed by space/EOL — citations sit before the split point or at end
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    checks = []
    def check(name, ok):
        checks.append((name, bool(ok)))

    check("length-18-35-sentences", 18 <= len(parts) <= 35)
    check("no-headings-or-lists", not re.search(r"^\s*(#|[-*]\s|\d+\.\s)", text, re.M))

    all_cits = _CIT.findall(text)
    check("has-citations", len(all_cits) >= 10)
    check("citations-valid-source-ids", all(c in SOURCES for c in all_cits))
    check("cites-all-three-sources", {"S1", "S2", "S3"} <= set(all_cits))

    src_nums = {k: nums(v) for k, v in SOURCES.items()}
    uncited_factual, ungrounded_numbers, miscited = 0, 0, 0
    for s in parts:
        cits = [c for c in _CIT.findall(s) if c in SOURCES]
        s_wo_cits = _CIT.sub("", s)
        n = nums(s_wo_cits)
        # a sentence containing any number is factual and must cite
        if n and not cits:
            uncited_factual += 1
            continue
        if n and cits:
            pool = set().union(*(src_nums[c] for c in cits))
            # normalize: 103 ms vs 103, 51.6, $0.032 -> regex already strips units/$
            if not n <= pool:
                ungrounded_numbers += 1
        # citing a source that shares zero content words with the sentence = suspicious miscite
        for c in cits:
            words = set(re.findall(r"[a-z]{4,}", s_wo_cits.lower()))
            swords = set(re.findall(r"[a-z]{4,}", SOURCES[c].lower()))
            if words and not (words & swords):
                miscited += 1
    check("all-numeric-sentences-cited", uncited_factual == 0)
    check("all-numbers-grounded-in-cited-source", ungrounded_numbers == 0)
    check("no-content-free-citations", miscited == 0)

    # coverage: the brief must actually convey the headline facts AND the limits
    low = text.lower()
    check("covers-gate-lift", ("88" in low and "100" in low))
    check("covers-objective-substance", ("51.6" in low and "103" in low))
    check("covers-cost-advantage", ("0.032" in low or "6 to 29" in low or "6–29" in low))
    check("covers-limits-single-file", "single-file" in low or "single file" in low)
    check("covers-polish-rejection", "93" in low)
    check("covers-not-tamper-proof", "tamper" in low)

    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        if not ok:
            print(f"FAIL {name}")
    print(f"gate: {passed}/{len(checks)}")
    return 0 if passed == len(checks) else 2

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
