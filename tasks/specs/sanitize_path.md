Write a single self-contained Python 3 file (stdlib only, shebang first, no external deps).

Implement exactly one public function:

    def sanitize_path(base: str, user_path: str) -> str | None

Semantics — a hardened path joiner used to safely place a user-supplied relative
path INSIDE a trusted base directory:

- On SAFE input, return the joined path as a string: `base` + the normalized
  `user_path`, where the result is strictly contained within `base`.
- On ANY unsafe input, return None. Unsafe means ANY of:
  * user_path is empty or only whitespace
  * user_path is an absolute path (starts with '/')
  * user_path contains a parent-directory traversal ('..' as a path component),
    INCLUDING traversal that only appears AFTER Unicode NFKC normalization
    (e.g. fullwidth dots U+FF0E that normalize to '.') — you MUST NFKC-normalize
    user_path before inspecting it
  * user_path contains a NUL byte ('\x00')
  * the normalized join would escape `base` (resolve outside it)

Be strict: when in doubt, return None. Do not touch the filesystem. Pure string logic.
