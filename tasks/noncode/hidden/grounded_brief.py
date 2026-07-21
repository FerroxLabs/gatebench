#!/usr/bin/env python3
"""HIDDEN gate for the grounded_brief non-code task. Never shown to any builder.

Targets the visible gate's blind spot: sentences whose numbers ARE grounded in the
cited source but whose CLAIM inverts or misstates what the source says. Every check
below is a claim-direction or attribution check that a fluent-but-wrong brief passes
the visible gate with. Prints FAIL lines + `hidden: N/M`; exit 0 iff all pass.
Authored and validated (reference must pass, fluent-but-wrong mutant must drop)
BEFORE any benchmark generation run. Stdlib only; fail-closed.
Usage: grounded_brief.py <artifact>"""
import re, sys

_CIT = re.compile(r"\[(S\d+)\]")
NEGATION = re.compile(r"\b(not|no|never|cannot|isn't|aren't|won't|neither)\b|n't\b", re.I)
UNGATED = re.compile(r"ungated|without (a |the )?gate|no gate|gate removed|run bare|one-shot|solo", re.I)
DECLINE = re.compile(r"reduc|dropp|drop |fell|lower|regress|cut |declin|degrad|cost it|down from|from 100", re.I)
ENTITIES = re.compile(r"openai|gpt|gemini|claude|anthropic|deepseek|kimi|qwen|llama|mistral|billion|million", re.I)


def sentences(text):
    text = re.sub(r"^```.*?\n|\n```$", "", text.strip(), flags=re.S)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def main(path):
    text = open(path, "r", encoding="utf-8").read()
    parts = sentences(text)
    checks = []

    def check(name, ok):
        checks.append((name, bool(ok)))

    tamper = [s for s in parts if "tamper" in s.lower()]
    # S3 says the gates are NOT tamper-proof; asserting the opposite must fail
    check("tamper-claim-negated", bool(tamper) and all(NEGATION.search(s) for s in tamper))
    polish = [s for s in parts if "93" in _CIT.sub("", s)]
    # 93 is the polish REGRESSION figure (down from 100); it must read as a decline
    check("polish-93-is-a-decline",
          bool(polish) and all(("100" in _CIT.sub("", s)) or DECLINE.search(s) for s in polish))
    lift = [s for s in parts if "88" in _CIT.sub("", s)]
    # 88 is the UNGATED pool's score; attributing it to the gated lane must fail
    check("88-attributed-to-ungated", bool(lift) and all(UNGATED.search(s) for s in lift))
    swap = True
    for s in parts:
        body = _CIT.sub("", s).lower()
        if "98" in body and "visible" in body and "hidden" not in body:
            swap = False
        if "88" in body and "hidden" in body and "visible" not in body:
            swap = False
    # 98 belongs to the hidden axis and 88/84 pair visible-first; swaps must fail
    check("no-visible-hidden-metric-swap", swap)
    mult = [s for s in parts if re.search(r"\b29\b", _CIT.sub("", s))]
    # the 6-to-29x multiple is the FRONTIER lane's cost premium, not the gated pool's
    check("29x-attributed-to-frontier",
          all(re.search(r"frontier|strongest", s, re.I) for s in mult))
    named = True
    for s in parts:
        body = _CIT.sub("", s).lower()
        if "51.6" in body and "maintainab" not in body:
            named = False
        if re.search(r"\b103\b", body) and not re.search(r"runtime|fastest|\bms\b|millisecond", body):
            named = False
    # grounded numbers still need the RIGHT metric name next to them
    check("objective-metrics-correctly-named", named)
    check("no-entities-outside-sources", not ENTITIES.search(text))

    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        if not ok:
            print(f"FAIL {name}")
    print(f"hidden: {passed}/{len(checks)}")
    return 0 if passed == len(checks) else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
