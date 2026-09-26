## 18.0.2.1.9 (2026-09-26)

- Fix: when a trigram index could not be built, the module replaced the
  `unaccent(text)` function of the `unaccent` extension with a SQL wrapper
  (only possible when Odoo connects as a PostgreSQL superuser). `pg_dump`
  does not keep that change: the restored extension is STABLE again and the
  restore fails on every index that uses `unaccent` (the Odoo database
  manager reports *Couldn't restore database*). The wrapper also used an
  unqualified dictionary, so on PostgreSQL 17 no index could be built on it.
  The module now only installs the missing extensions and logs a warning.
- The trigram indexes are attempted only when `pg_trgm` is installed and
  `public.unaccent(text)` is IMMUTABLE, without flushing pending
  computations, and the warning is logged once per index. The helper runs
  from `init()` of every module that extends the product models; a failing
  `CREATE INDEX` followed by a flushing savepoint aborted the transaction
  when a later module had a stored computed field whose column did not exist
  yet (registry failed to load while installing `deltatech_sale_multiple`).
- A warning is logged at module update when the extension's `unaccent(text)`
  was already replaced. To fix such a database, run as a superuser, then
  restart Odoo:

  ```sql
  DROP EXTENSION unaccent CASCADE;  -- drops the indexes that use unaccent
  CREATE SCHEMA IF NOT EXISTS unaccent_schema;
  CREATE EXTENSION unaccent SCHEMA unaccent_schema;
  CREATE FUNCTION public.unaccent(text) RETURNS text
      LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
      AS $$ SELECT unaccent_schema.unaccent('unaccent_schema.unaccent'::regdictionary, $1) $$;
  ```

  Then update the modules that declare the dropped indexes (`-u`). This is
  the layout odoo.sh uses, and it survives a dump/restore.
- Added an index on `product.alternative.product_tmpl_id`. Reading the codes
  of a product scanned the whole table: 39.8 ms against 0.16 ms on 1.36
  million codes.

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
