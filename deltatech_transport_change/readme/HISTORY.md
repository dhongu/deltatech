## 19.0.0.1.5 (2026-09-23)

- `except: pass` blocks replaced with `contextlib.suppress` for the same exceptions;
  behavior is unchanged. The test tear-downs use the same pattern.
