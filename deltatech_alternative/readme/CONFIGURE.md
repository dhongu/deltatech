## Alternative Search Settings

Navigate to **Settings > Inventory** (the setting is injected after the *Units of Measure*
section) to configure the alternative-code search behaviour:

| Setting | System Parameter | Default | Effect |
|---|---|---|---|
| **Alternative Search** (checkbox) | `alternative.search_name` | disabled | When enabled, product name-search queries also scan alternative codes. |
| **Alternative Limit** | `alternative.limit` | 10 | Maximum number of extra results returned from the alternative-code search. |
| **Minimum Length** | `alternative.length_min` | 3 | Minimum number of characters the user must type before the alternative search is triggered. |

These three values are stored as `ir.config_parameter` system parameters and can also be
set directly via **Settings > Technical > Parameters > System Parameters** if needed.

## Large Databases (Index on Alternative Codes)

Alternative codes (`product.alternative.name`) use a trigram (GIN) index, so a search
such as `ilike '%4561%'` does not scan the whole table.

- The PostgreSQL extension `pg_trgm` must be available. Without it Odoo creates no index
  on the column.
- Odoo adds `unaccent` to the index only when `public.unaccent(text)` is `IMMUTABLE`.
  Otherwise the index is created without it and the search, which calls
  `unaccent(name) ILIKE unaccent(...)`, cannot use it. Odoo logs *PostgreSQL function
  'unaccent' is present but not immutable* in that case.

### Checking `unaccent`

```sql
SELECT oid::regprocedure, provolatile FROM pg_proc WHERE proname = 'unaccent';
```

- **odoo.sh** needs nothing: the extension lives in `unaccent_schema` and the platform
  adds an `IMMUTABLE` wrapper `public.unaccent(text)` (`provolatile = i`).
- **Self-hosted**, with the extension installed in `public`, `unaccent(text)` is `STABLE`
  (`s`). Do **not** use `ALTER FUNCTION public.unaccent(text) IMMUTABLE`, and do not
  replace the extension's function: the change is part of the extension, `pg_dump` does
  not keep it, and restoring the database fails on every index that uses `unaccent`
  (*functions in index expression must be marked IMMUTABLE*). The Odoo database manager
  then reports *Couldn't restore database*.

### Setting up `unaccent` like odoo.sh (self-hosted)

Run as a superuser, then restart Odoo (it reads the function status at startup). The
script moves the extension to its own schema, adds the `IMMUTABLE` wrapper and rebuilds
the indexes that used the extension's function. Rebuilding blocks writes on those tables,
so run it in a maintenance window.

```sql
BEGIN;
CREATE SCHEMA IF NOT EXISTS unaccent_schema;
ALTER EXTENSION unaccent SET SCHEMA unaccent_schema;
CREATE FUNCTION public.unaccent(text) RETURNS text
    LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
    AS $$ SELECT unaccent_schema.unaccent('unaccent_schema.unaccent'::regdictionary, $1) $$;
DO $$
DECLARE r record;
BEGIN
    FOR r IN
        SELECT DISTINCT i.indexrelid::regclass AS idx, pg_get_indexdef(i.indexrelid) AS def
        FROM pg_index i
        JOIN pg_depend d ON d.classid = 'pg_class'::regclass AND d.objid = i.indexrelid
        WHERE d.refclassid = 'pg_proc'::regclass
          AND d.refobjid = 'unaccent_schema.unaccent(text)'::regprocedure
    LOOP
        EXECUTE format('DROP INDEX %s', r.idx);
        EXECUTE replace(r.def, 'unaccent_schema.unaccent(', 'public.unaccent(');
    END LOOP;
END $$;
COMMIT;
```

The dictionary is schema-qualified on purpose. With a bare `'unaccent'`, PostgreSQL 17
cannot build the index (index builds run with a restricted `search_path`) and older
versions fail on restore.

Trigram indexes created while `unaccent` was `STABLE` do not contain `unaccent`. Odoo
compares only the access method (`gin`), not the expression, so it keeps them although
the search cannot use them. Drop them after the change and update the modules that
declare them (`-u`).

### Creating the index on a large table

With millions of codes, create the index before updating the module, so writes are not
blocked while it is built:

```sql
DROP INDEX IF EXISTS product_alternative__name_index;
CREATE INDEX CONCURRENTLY product_alternative__name_index
    ON product_alternative USING gin (unaccent(name) gin_trgm_ops);
```

Leave out `unaccent(...)` if `public.unaccent(text)` is not `IMMUTABLE`. Odoo finds an
index with the expected name and access method and does not rebuild it.

Databases migrated from 18.0 already have the same index under another name
(`product_alternative_name_unaccent_gin`, created by the 18.0 module). Rename it instead
of building a new one:

```sql
DROP INDEX IF EXISTS product_alternative__name_index;
ALTER INDEX product_alternative_name_unaccent_gin RENAME TO product_alternative__name_index;
```
