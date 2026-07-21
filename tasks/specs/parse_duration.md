Write a single self-contained Python 3 file (stdlib only, shebang first, no external deps).

Implement exactly one public function:

    def parse_duration(s: str) -> int | None

It parses a compact human duration string into a total number of SECONDS.

Grammar (STRICT):
- A duration is one or more unit-terms concatenated, e.g. "1h30m", "90m", "2h", "45s", "1h2m3s".
- Each term is a non-negative integer followed immediately by a unit letter: 'h' (hours),
  'm' (minutes), or 's' (seconds). Hours=3600s, minutes=60s, seconds=1s.
- Units, when present, MUST appear in strict descending order h -> m -> s, and each unit may
  appear AT MOST once. "30m1h" is invalid (out of order); "1h1h" is invalid (repeat).
- Return the total integer seconds on valid input.
- Return None on ANY invalid input, including: empty or whitespace-only; leading/trailing/inner
  whitespace ("1h 30m" is invalid); a bare number with no unit ("90"); an unknown unit ("5d");
  a unit with no number ("h"); negative sign; non-ASCII digits; any leftover unparsed characters.

Be strict: when in doubt, return None. Pure string logic, no I/O.
