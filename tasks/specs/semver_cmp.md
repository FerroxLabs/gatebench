Write a single self-contained Python 3 file (stdlib only, shebang first, no external deps).
Do NOT use any packaging/semver library. Implement the logic yourself.

Implement exactly two public functions:

    def is_valid(v: str) -> bool
    def compare(a: str, b: str) -> int

They implement Semantic Versioning 2.0.0 (https://semver.org) validity and precedence.

VERSION GRAMMAR (is_valid returns True iff `v` matches this exactly):
    <version> ::= <major> "." <minor> "." <patch>
                  [ "-" <prerelease> ] [ "+" <build> ]
- major/minor/patch: numeric identifiers with NO leading zeros (a single "0" is allowed; "01" is not).
- prerelease: dot-separated identifiers, each either:
    * numeric (only digits, NO leading zeros; a lone "0" allowed), or
    * alphanumeric: contains only [0-9A-Za-z-] and is NOT a leading-zero number
      (i.e. any identifier containing a non-digit is valid as-is, including "-" and letters).
    An empty identifier (e.g. "1.0.0-" or "1.0.0-a..b") is INVALID.
- build: dot-separated identifiers, each non-empty and only [0-9A-Za-z-]; leading zeros ARE allowed
  in build identifiers (build metadata has no numeric interpretation). Empty identifier invalid.

compare(a, b) returns -1 if a < b, 0 if a == b (equal PRECEDENCE), 1 if a > b, per SemVer §11:
- If either a or b is not valid, raise ValueError.
- Compare major, then minor, then patch numerically.
- A version WITH a prerelease has LOWER precedence than the same version WITHOUT one
  (1.0.0-alpha < 1.0.0).
- Compare prerelease identifiers left to right:
    * numeric identifiers compared numerically;
    * alphanumeric identifiers compared lexically in ASCII order;
    * numeric identifier ALWAYS has lower precedence than an alphanumeric identifier;
    * a larger set of pre-release fields has higher precedence if all preceding are equal
      (1.0.0-alpha < 1.0.0-alpha.1).
- BUILD METADATA IS IGNORED for precedence (1.0.0+a == 1.0.0+b, and == 1.0.0).

Both functions must never raise except compare's documented ValueError on invalid input.
Pure computation, no I/O.
