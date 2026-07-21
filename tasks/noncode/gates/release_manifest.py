#!/usr/bin/env python3
"""Tier-2 (Formal/schema) gate for the release_manifest proof task.
Usage: release_manifest.py <artifact.json>  — prints FAIL lines + `gate: N/M`, exit 0 iff all pass.
Orchestrator-authored; stdlib only; fail-closed."""
import json, re, sys

def main(path):
    checks = []
    def check(name, ok):
        checks.append((name, bool(ok)))

    raw = open(path, "r", encoding="utf-8").read()
    m = re.search(r"```json\s*(.*?)```", raw, re.S)
    body = m.group(1) if m else raw
    try:
        doc = json.loads(body)
        check("parses-strict-json", True)
    except Exception:
        check("parses-strict-json", False)
        doc = None

    if isinstance(doc, dict):
        keys = set(doc.keys())
        want = {"name", "version", "released", "channel", "artifacts", "checksums",
                "min_runtime", "breaking_changes", "signature"}
        check("exact-top-level-keys", keys == want)
        check("name-forgectl", doc.get("name") == "forgectl")
        check("version-semver-240", doc.get("version") == "2.4.0")
        check("released-iso-date", doc.get("released") == "2026-07-21")
        check("channel-stable", doc.get("channel") == "stable")

        arts = doc.get("artifacts")
        ok_arts = isinstance(arts, list) and len(arts) == 3
        check("artifacts-exactly-3", ok_arts)
        plats = {"darwin-arm64", "linux-x86_64", "windows-x86_64"}
        seen, fn_ok, size_ok = set(), True, True
        fnames = []
        if ok_arts:
            for a in arts:
                if not isinstance(a, dict):
                    fn_ok = size_ok = False
                    continue
                p = a.get("platform")
                seen.add(p)
                ext = "zip" if p == "windows-x86_64" else "tar.gz"
                expect = f"forgectl-2.4.0-{p}.{ext}"
                if a.get("filename") != expect:
                    fn_ok = False
                fnames.append(a.get("filename"))
                if not (isinstance(a.get("size_bytes"), int) and a["size_bytes"] > 1000000):
                    size_ok = False
        check("artifact-platforms-complete", seen == plats)
        check("artifact-filenames-exact", fn_ok and ok_arts)
        check("artifact-sizes-int-gt-1mb", size_ok and ok_arts)

        cks = doc.get("checksums")
        ck_keys = isinstance(cks, dict) and set(cks.keys()) == set(fnames) and len(fnames) == 3
        check("checksum-keys-match-filenames", ck_keys)
        hex64 = re.compile(r"^[0-9a-f]{64}$")
        check("checksums-sha256-shape",
              ck_keys and all(isinstance(v, str) and hex64.match(v) for v in cks.values()))

        check("min-runtime-node", doc.get("min_runtime") == {"node": ">=20.0.0"})

        bc = doc.get("breaking_changes")
        check("breaking-changes-1-to-3",
              isinstance(bc, list) and 1 <= len(bc) <= 3
              and all(isinstance(s, str) and 0 < len(s) <= 120 for s in bc))

        sig = doc.get("signature")
        sig_ok = (isinstance(sig, dict) and sig.get("alg") == "ed25519"
                  and isinstance(sig.get("key_id"), str) and sig.get("key_id")
                  and isinstance(sig.get("sig"), str) and len(sig.get("sig", "")) == 88
                  and sig.get("sig", "").endswith("=")
                  and re.match(r"^[A-Za-z0-9+/]{87}=$", sig.get("sig", "")))
        check("signature-ed25519-shape", bool(sig_ok))

        def no_null(x):
            if x is None:
                return False
            if isinstance(x, dict):
                return all(no_null(v) for v in x.values())
            if isinstance(x, list):
                return all(no_null(v) for v in x)
            return True
        check("no-null-values", no_null(doc))
    else:
        for name in ["exact-top-level-keys", "name-forgectl", "version-semver-240",
                     "released-iso-date", "channel-stable", "artifacts-exactly-3",
                     "artifact-platforms-complete", "artifact-filenames-exact",
                     "artifact-sizes-int-gt-1mb", "checksum-keys-match-filenames",
                     "checksums-sha256-shape", "min-runtime-node", "breaking-changes-1-to-3",
                     "signature-ed25519-shape", "no-null-values"]:
            check(name, False)

    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        if not ok:
            print(f"FAIL {name}")
    print(f"gate: {passed}/{len(checks)}")
    return 0 if passed == len(checks) else 2

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
