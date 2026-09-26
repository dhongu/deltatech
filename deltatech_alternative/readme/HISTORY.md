## 19.0.2.1.3 (2026-09-26)

- The index on `product.alternative.name` is now a trigram (GIN) index
  instead of btree. Product search runs `ilike '%code%'`, which the btree
  index could not serve (sequential scan: 169 ms against 4.6 ms with GIN on
  1.36 million codes), and btree rejects values over ~2,700 bytes. The
  existing btree index is replaced when the module is updated. On large
  databases, see *Large Databases* in the configuration notes.
- Removed `index=True` from the computed, non-stored `alternative_code` field,
  where it had no effect.

## 19.0.2.1.2 (2026-09-26)

- Ported from 18.0: the daily *Alternative: Split multi-code records* cron and
  the `product.alternative.split_multi_codes()` method, which split a record
  holding several codes on one line (`A; B, C`) into one record per code. The
  first code stays on the original record; the others inherit its product,
  sequence and hide flag.
- The cron is inactive by default on new installations. Activate it in
  *Settings > Technical > Scheduled Actions* when needed.
- Codes are split only on `;` and `,`. Spaces are never a delimiter, because
  many OEM part numbers contain them (`366 200 05 01`).
- A single code surrounded by stray delimiters (`12345, `) is cleaned up in
  place.
- New compared to 18.0: codes the product already has, or that repeat on the
  same line, are no longer created again. The batch size can be passed as
  `split_multi_codes(limit=...)` (default 5000).
- On databases migrated from 18.0 the existing cron record (same XML id) is
  reused and keeps its current active/inactive state (`noupdate`). It had
  stopped working because the method was missing on 19.0.
