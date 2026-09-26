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
- Odoo adds `unaccent` to the index only when the `unaccent` function is `IMMUTABLE`.
  Otherwise the index is created without it and the search, which calls
  `unaccent(name) ILIKE unaccent(...)`, cannot use it. To fix this, run as a superuser:

  ```sql
  ALTER FUNCTION public.unaccent(text) IMMUTABLE;
  ```

- With millions of codes, create the index before updating the module, so writes are not
  blocked while it is built:

  ```sql
  DROP INDEX IF EXISTS product_alternative__name_index;
  CREATE INDEX CONCURRENTLY product_alternative__name_index
      ON product_alternative USING gin (unaccent(name) gin_trgm_ops);
  ```

  Leave out `unaccent(...)` if the function is not `IMMUTABLE`. Odoo finds an index with
  the expected name and access method (`gin`) and does not rebuild it.
- Odoo compares only the access method, not the expression. An existing GIN index created
  without `unaccent` is kept but not used by the search. Drop it by hand after making
  `unaccent` `IMMUTABLE`, then create it again as above.
