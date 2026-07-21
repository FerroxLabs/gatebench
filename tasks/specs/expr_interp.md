Write a single self-contained Python 3 file (stdlib only, shebang first, no external deps).
Do NOT use eval/exec/compile or the ast module. Implement your own tokenizer + parser + evaluator.

Implement exactly one public function:

    def run_program(src: str) -> dict | None

It interprets a tiny expression language and returns the final variable environment as a dict
mapping variable name (str) -> integer value (int), or None if the program is invalid.

The language is a sequence of statements separated by ';'. A trailing ';' is allowed. Two kinds
of statement:
  - assignment:   NAME = EXPR
  - bare expr:    EXPR            (evaluated for effect/errors; does not bind a name)

Whitespace (ASCII spaces, tabs, newlines) is insignificant except inside no token.
An empty program (no statements, or only whitespace/semicolons) returns an empty dict {}.

NAME: an identifier matching [A-Za-z_][A-Za-z0-9_]* .

EXPR supports (and ONLY these):
- non-negative integer literals (one or more ASCII digits; no leading-zero restriction)
- variable references (a NAME previously assigned in this program)
- binary operators: +  -  *  //  %  **
- unary minus (e.g. -3, 2*-3, --2 == 2)
- parentheses for grouping

Semantics MUST match Python integer arithmetic exactly:
- precedence: ** highest, then unary minus, then * // %, then + -
- ** is RIGHT-associative (2**3**2 == 512); * // % and + - are LEFT-associative
- // is floor division, % is modulo, results are always int
- assignment binds after fully evaluating the right-hand side; later statements see the binding
- referencing a NAME that was never assigned is an ERROR (return None for the whole program)

Return None on ANY invalid program, including: a reference to an undefined variable; division or
modulo by zero; assignment target that is not a bare NAME (e.g. `1 = 2`, `a+b = 3`); a malformed
expression (trailing operator, empty parens, two literals in a row, unbalanced parens); an unknown
character; or a keyword used where a value is required. Be strict: when in doubt, return None.

Determinism: the returned dict's contents depend only on `src`. Pure computation, no I/O.
