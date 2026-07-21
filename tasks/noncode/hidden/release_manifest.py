#!/usr/bin/env python3
"""HIDDEN gate for the release_manifest non-code task. Never shown to any builder.

Targets the visible gate's blind spot: fields that are schema-valid but semantically
wrong. A manifest can clear all 16 visible checks with placeholder checksums, a
degenerate signature, filler key ids, cloned sizes, and duplicated changelog lines.
These 7 checks catch that. Prints FAIL lines + `hidden: N/M`; exit 0 iff all pass.
Authored and validated (reference must pass, fluent-but-wrong mutant must drop)
BEFORE any benchmark generation run. Stdlib only; fail-closed.
Usage: release_manifest.py <artifact>"""
import json, re, sys

NAMES = ["checksums-pairwise-distinct", "checksums-plausible-entropy",
         "signature-not-degenerate", "key-id-not-filler",
         "sizes-pairwise-distinct", "breaking-changes-distinct-substantive",
         "no-template-markers"]

FILLER_KEY_IDS = {"key", "keyid", "key_id", "key-id", "string", "id", "test",
                  "example", "sample", "abc", "abcd", "1234", "todo", "placeholder"}
MARKER = re.compile(r"TODO|FIXME|CHANGEME|PLACEHOLDER|REPLACE[_ ]?ME|YOUR[_ ]", re.I)


def distinct_chars(s):
    return len(set(s or ""))


def main(path):
    raw = open(path, "r", encoding="utf-8").read()
    m = re.search(r"```json\s*(.*?)```", raw, re.S)
    body = m.group(1) if m else raw
    try:
        doc = json.loads(body)
    except Exception:
        doc = None
    results = {}
    if isinstance(doc, dict):
        cks = doc.get("checksums") if isinstance(doc.get("checksums"), dict) else {}
        vals = [v for v in cks.values() if isinstance(v, str)]
        results["checksums-pairwise-distinct"] = len(vals) == 3 and len(set(vals)) == 3
        # a real sha256 hex digest uses most of the 16 hex digits; placeholders do not
        results["checksums-plausible-entropy"] = (
            len(vals) == 3 and all(distinct_chars(v) >= 8 for v in vals))

        sig = doc.get("signature") if isinstance(doc.get("signature"), dict) else {}
        sv = sig.get("sig") if isinstance(sig.get("sig"), str) else ""
        results["signature-not-degenerate"] = distinct_chars(sv.rstrip("=")) >= 8
        kid = sig.get("key_id") if isinstance(sig.get("key_id"), str) else ""
        results["key-id-not-filler"] = (
            len(kid) >= 4 and kid.lower() not in FILLER_KEY_IDS
            and not re.search(r"[<>{}]", kid))

        arts = doc.get("artifacts") if isinstance(doc.get("artifacts"), list) else []
        sizes = [a.get("size_bytes") for a in arts if isinstance(a, dict)]
        results["sizes-pairwise-distinct"] = len(sizes) == 3 and len(set(sizes)) == 3

        bc = doc.get("breaking_changes") if isinstance(doc.get("breaking_changes"), list) else []
        strs = [s for s in bc if isinstance(s, str)]
        results["breaking-changes-distinct-substantive"] = (
            len(strs) == len(bc) and len(bc) >= 1
            and len({s.strip().lower() for s in strs}) == len(strs)
            and all(len(s.split()) >= 4 for s in strs))

        scan = [str(doc.get("name")), str(doc.get("version")), str(doc.get("channel")),
                kid] + strs + [str(a.get("filename")) for a in arts if isinstance(a, dict)]
        results["no-template-markers"] = not any(MARKER.search(s) for s in scan)
    passed = 0
    for name in NAMES:
        ok = bool(results.get(name, False))
        passed += ok
        if not ok:
            print(f"FAIL {name}")
    print(f"hidden: {passed}/{len(NAMES)}")
    return 0 if passed == len(NAMES) else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
