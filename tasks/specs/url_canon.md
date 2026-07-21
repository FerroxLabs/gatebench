Write a single self-contained Python 3 file (stdlib only, shebang first, no external deps).
Do NOT use urllib's parsing/normalization to do the whole job for you — you may use urllib only
for percent-encoding helpers if you wish, but implement the canonicalization logic yourself.

Implement exactly one public function:

    def canonicalize(url: str) -> str | None

It returns a canonical form of an absolute http/https URL, or None if the input is not an
acceptable absolute http(s) URL. This is a security-relevant normalizer (think SSRF allow-listing):
when in doubt, return None.

Accept ONLY absolute URLs of the form:  scheme "://" host [":" port] [path] [ "?" query ] [ "#" frag ]
- scheme: case-insensitive "http" or "https"; anything else (ftp, file, javascript, relative, no
  scheme) -> None.
- host: a non-empty registered name or IPv4. Lowercase it. Reject a host containing a userinfo
  component ("user@host") -> None (credentials in URLs are rejected). Reject an empty host -> None.
- port: optional. If present it must be all digits. Remove the port if it is the DEFAULT for the
  scheme (80 for http, 443 for https); otherwise keep it as ":<digits>" with any leading zeros
  stripped (":080" -> ":80", ":00" -> None because 0 is not a real port; ports must be 1..65535).
  A non-numeric or out-of-range port -> None.

Canonicalization of the remainder:
- If there is no path, the canonical path is "/".
- Normalize the path by resolving "." and ".." segments (like a filesystem):
    * "." segments are removed;
    * ".." pops the previous real segment; a ".." that would escape the root ("/../a") is
      clamped at root (NOT allowed to go above "/"), yielding "/a".
    * Preserve a trailing slash only if the original last segment was "." or ".." resolving to a
      directory, OR the original path ended in "/". Collapse duplicate slashes ("//" -> "/").
- Percent-encoding: uppercase the hex digits of any %XY escape ("%2f" -> "%2F"). Do NOT decode
  reserved characters. Leave already-safe characters as-is.
- Drop an empty query ("?" with nothing after) and an empty fragment ("#..."): a trailing "?" or
  "#" with no content is removed. A non-empty query/fragment is preserved verbatim (after the
  percent-hex uppercasing rule) and its leading "?"/"#" kept.
- The scheme is lowercased and the output uses "://".

Return None on any input that does not parse as an absolute http(s) URL by the above rules.
The function must never raise for any `str` input. Pure computation, no I/O.
