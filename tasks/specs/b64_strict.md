Write a single self-contained Python 3 file (stdlib only, shebang first, no fences, no commentary).
Do NOT import base64, binascii, or any decoding library — implement the decode yourself.

Implement exactly one public function:

    def b64decode_strict(s: str) -> bytes | None

Strictly decode STANDARD base64 (alphabet A-Z a-z 0-9 + / with '=' padding) into bytes, or return None
if `s` is not strictly-valid base64.

Strict rules (return None on ANY violation):
- length must be a multiple of 4 (empty string is valid and decodes to b'').
- only the standard alphabet plus '=' padding; '=' may appear ONLY as 1 or 2 chars at the very end.
- no characters after padding; no interior '='.
- the bits that padding forces to zero must actually be zero is NOT required — accept canonical encodings
  as produced by a standard encoder.
Return the decoded bytes on success.
