Write a single self-contained Python 3 file (stdlib only, shebang first, no external deps).

Implement exactly one public function:

    def is_safe_redirect(allowed_host: str, target: str) -> str | None

It validates a post-login redirect target to prevent OPEN REDIRECT / SSRF. Return `target`
UNCHANGED if it is a safe same-site redirect; otherwise return None.

SAFE means EITHER:
  (a) a site-relative path: starts with a single '/', but NOT '//' and NOT '/\' (backslash), and
      contains no ASCII control chars or whitespace; or
  (b) an absolute URL whose scheme is exactly http or https (case-insensitive) AND whose host
      EXACTLY equals allowed_host (case-insensitive) — exact host, not a subdomain and not a suffix.

Return None for ANYTHING else, including (these are the attacks you MUST block):
  - scheme-relative '//evil.com/x'
  - backslash tricks '/\evil.com', '\\evil.com'
  - absolute URL to a different host 'https://evil.com/x'
  - userinfo trick 'https://allowed.com@evil.com' (the real host is evil.com)
  - suffix trick 'https://allowed.com.evil.com'
  - subdomain 'https://sub.allowed.com' (exact host required)
  - non-http scheme 'javascript:alert(1)', 'data:text/html,...'
  - empty/whitespace-only target
  - any target containing an ASCII control char (e.g. newline, tab, NUL)

Use urllib.parse for absolute URLs; compare the parsed hostname, never a substring. Be strict.
