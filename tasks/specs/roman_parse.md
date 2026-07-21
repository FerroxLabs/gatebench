Write a single self-contained Python 3 file (stdlib only, shebang first, no fences, no commentary).
Do NOT import any roman-numeral library.

Implement exactly one public function:

    def roman_parse(s: str) -> int | None

Parse a STRICT, CANONICAL Roman numeral (value 1..3999) and return its integer value, or None if the
string is not a valid canonical Roman numeral.

Rules (be strict — canonical form ONLY):
- Uppercase letters only: I V X L C D M.
- Subtractive pairs allowed ONLY: IV(4) IX(9) XL(40) XC(90) CD(400) CM(900).
- Repetition: I, X, C, M at most 3 times in a row; V, L, D never repeated.
- The numeral must be the UNIQUE canonical representation of its value — e.g. "IIII", "VV", "IL",
  "IC", "XM", "VX", "MMMM" (>3999) are all INVALID -> None.
- Empty string, lowercase, or any non-Roman character -> None.
