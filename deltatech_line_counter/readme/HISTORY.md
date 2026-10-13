## 19.0.1.0.2 (2026-10-02)

- The module name in the result is HTML-escaped. Unreadable files are skipped explicitly (`OSError`/`UnicodeDecodeError`, logged at debug level) instead of swallowing every exception. The description states that the line count is an estimate. Tests added for the count, the skipped files and the escaping.

## 19.0.1.0.1 (2026-09-30)

- New module icon in the flat style of the other modules; it replaces the old one.
