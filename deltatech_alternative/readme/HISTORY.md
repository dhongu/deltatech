## 18.0.2.1.8 (2026-07-27)

- Fix: the daily *Alternative: Split multi-code records* cron treated a space as
  a code delimiter, so every alternative code containing spaces was exploded
  into meaningless fragments. An OEM code such as
  `366 200 05 01 MERCEDES 366 200 15 01 MERCEDES` became `366`, `200`, `05`,
  `01`, `MERCEDES`, ... — the original code no longer existed in the database
  and the product could not be found by it any more. Because the cron runs
  daily, it also re-broke records that had been repaired manually.
  Codes are now split only on explicit delimiters (`;` and `,`).
- A single code surrounded by stray delimiters (`12345, `) is now cleaned up in
  place instead of being left untouched.
- Tests: replaced the space-splitting test with tests asserting that codes
  containing spaces are preserved, plus tests for stray delimiters.
