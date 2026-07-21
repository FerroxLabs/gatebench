Write a single self-contained Python 3 file (stdlib only, shebang first, no external deps).
Do NOT use eval/exec/compile or the ast module. Implement your own parser.

Implement exactly one public function:

    def safe_eval(expr: str) -> int | None

It evaluates an integer arithmetic expression and returns the integer result, or None if the
expression is invalid or cannot be evaluated.

Supported (and ONLY these):
- non-negative integer literals (one or more ASCII digits)
- binary operators: +  -  *  //  %  **   (note: // is integer division, % is modulo, ** is power)
- unary minus (e.g. -3, 2*-3, --2 == 2)
- parentheses for grouping
- optional ASCII spaces between tokens (they are insignificant)

Semantics MUST match Python's integer arithmetic exactly:
- precedence: ** highest, then unary minus, then * // %, then + -
- ** is RIGHT-associative (2**3**2 == 512); the others are left-associative
- integer results only

Return None on ANY invalid input, including: empty/whitespace-only; a single '/' (only '//' is
valid); any letter or unsupported character; unbalanced parentheses; a malformed expression
(trailing operator, empty parens, two literals in a row); and DIVISION OR MODULO BY ZERO.

Be strict: when in doubt, return None. Pure computation, no I/O.
