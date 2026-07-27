# Products Alternative

Module that extends the standard Odoo product with support for **alternative codes** (cross-references, supplier codes, customer codes, etc.).

## Features

### Alternative Codes on Product

- Each product (template or variant) can have one or more alternative codes stored in the `product.alternative` model.
- The `alternative_code` computed field on `product.template` / `product.product` displays all codes joined by `"; "` and allows inline editing when there is a single alternative record.
- Codes can be marked as **hidden** (`hide = True`) so they are excluded from the displayed `alternative_code` value.

### Product Search by Alternative Code

- `name_search` on `product.template` and `product.product` is extended to also search through alternative codes.
- `_search_display_name` is extended to include alternative codes in domain-based searches.
- Search by alternative code is enabled via the system parameter `alternative.search_name` (set to `True` to activate).

### Product Catalog (`product.catalog`)

- New model for large master-data catalogs of products.
- When searching for a product by code returns no results, an additional lookup is made in the catalog; if found, a new product is automatically generated from the catalog entry.

### Used For Field

- New `used_for` field on `product.template` to document what the product is typically used for (free-text).

### Multi-code Split (Cron)

- A scheduled action runs **daily** and processes batches of up to **5 000** `product.alternative` records at a time.
- It detects records where the `name` field contains multiple codes on a single line, separated by **semicolons** (`;`) or **commas** (`,`).
- Each such record is split into individual records — one per code — preserving `product_tmpl_id`, `sequence`, and `hide` from the original record.
- **Spaces are never treated as a separator**: many OEM part numbers contain spaces (for example `366 200 05 01`), so a code is only split on an explicit delimiter.
- A single code surrounded by stray delimiters (`12345, `) is cleaned up in place, without creating extra records.
- The cron repeats on subsequent days until all multi-code records have been normalised.

## Configuration

| Parameter | Model | Default | Effect |
|---|---|---|---|
| `alternative.search_name` | `ir.config_parameter` | `False` | Enable search by alternative code |

## Views Extended

- Product Template form: alternative codes tab, `used_for` field
- Product Variant form: alternative codes tab
- Sale Order line: alternative code column
- Purchase Order line: alternative code column
- Stock Move / Picking: alternative code column
