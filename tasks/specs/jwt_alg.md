Write a single self-contained Python 3 file (stdlib only, shebang first, no external deps).

Implement exactly one public function:

    def choose_verifier(header_json: str) -> str | None

Given a JWT header as a JSON string, return the signing algorithm to use, or None if the token
must be REJECTED. This defends against the classic JWT `alg=none` bypass and algorithm-confusion
downgrade attacks.

Accept ONLY if the parsed header's "alg" is a STRING that is EXACTLY one of the asymmetric
allowlist: "RS256" or "ES256". Return that alg string.

Return None for ANYTHING else, including:
  - alg "none" in ANY case ("none","None","NONE","nOnE")
  - alg "HS256" or any symmetric/other alg not in the allowlist (downgrade/confusion)
  - alg with different case ("rs256") or surrounding whitespace ("RS256 ")
  - "alg" missing entirely
  - "alg" present but not a string (a number, list, object, bool, null)
  - malformed / empty JSON

Be strict: exact, case-sensitive match against the allowlist; when in doubt, None.
