# Task: release-manifest.json (structured-gen, Tier-2 proof)

Produce a single JSON document (no prose, no fences beyond one ```json block) — a release manifest
for a fictional CLI tool `forgectl` version 2.4.0 released 2026-07-21, satisfying ALL constraints:

1. Top-level object with EXACTLY these keys: `name`, `version`, `released`, `channel`, `artifacts`,
   `checksums`, `min_runtime`, `breaking_changes`, `signature`.
2. `name` = "forgectl". `version` = "2.4.0" (semver 2.0, no leading v).
3. `released` = ISO-8601 date "2026-07-21".
4. `channel` ∈ {"stable","beta","nightly"} — must be "stable".
5. `artifacts`: array of EXACTLY 3 objects, one per platform `darwin-arm64`, `linux-x86_64`,
   `windows-x86_64`; each has `platform`, `filename`, `size_bytes` (integer > 1000000).
   `filename` must be `forgectl-2.4.0-<platform>.tar.gz` (`.zip` for windows).
6. `checksums`: object mapping each artifact filename → 64-char lowercase hex string (sha256 shape).
   Keys must exactly match the 3 filenames.
7. `min_runtime`: object `{ "node": ">=20.0.0" }`.
8. `breaking_changes`: array of at least 1 and at most 3 non-empty strings, each ≤ 120 chars.
9. `signature`: object `{ "alg": "ed25519", "key_id": <non-empty string>, "sig": <88-char base64
   string ending in '='> }`.
10. The JSON must parse strictly (json.loads), contain no additional top-level keys, and use no
    null values anywhere.
