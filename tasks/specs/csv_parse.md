Write a single self-contained Python 3 file (stdlib only, shebang first, no external deps).
Do NOT use the `csv` module or any external library. Implement the parser yourself.

Implement exactly one public function:

    def parse_csv(text: str) -> list[list[str]]

It parses RFC-4180-style CSV text into a list of records, each a list of string fields.

Rules (follow exactly):
- Fields are separated by commas ','. Records are separated by a line break, which may be
  "\r\n" (CRLF) or "\n" (LF); treat both as a single record separator (do not mix into fields).
- A field may be enclosed in double quotes '"'. Inside a quoted field:
    * a literal double quote is written as two double quotes ("") and decodes to one '"';
    * commas and line breaks (CRLF or LF) are literal content, NOT separators.
- An unquoted field is taken verbatim up to the next comma or record separator. Leading/trailing
  spaces in an unquoted field are PRESERVED (do not strip).
- The empty string "" as input yields [] (zero records).
- A final trailing record separator does NOT create an extra empty trailing record
  (e.g. "a,b\n" -> [["a","b"]], not [["a","b"],[""]]).
- A blank line in the middle (just a record separator) IS a record with a single empty field: [""].
- Every record you emit must have at least one field; a line "a," yields ["a",""] (two fields).

Robustness / errors:
- If a quoted field is opened but never closed before end of input, treat end of input as closing
  it (emit the accumulated content) rather than raising — the function must not throw on any str.
- Characters after a closing quote and before the next comma/separator (e.g. `"a"b`) are appended
  as literal content of that field (lenient concatenation): `"a"b` -> `ab`.

The function must never raise for any `str` input, and must return a list of lists of str.
Pure computation, no I/O.
