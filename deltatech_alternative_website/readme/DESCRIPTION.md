This module extends the Odoo website shop to expose **alternative product codes** directly on the product page and in the website search engine. It is designed for businesses (spare parts distributors, industrial suppliers) where customers search by OEM codes, cross-reference numbers, or manufacturer codes rather than internal SKUs.

**Key features:**

- Displays the alternative code(s) stored on the product (`alternative_ids`) as hidden `<span>` elements with `itemprop="alternateName"`, making them available to search engines and the internal site search.
- Shows a dedicated **"Alternative code"** section on the product page (visible to logged-in users only) with the primary `alternative_code` value.
- Shows a **"Used For"** section on the product page when the `used_for` field is populated, indicating the vehicle / equipment the part fits.
- Extends the website full-text search (`_search_get_detail`) to include `alternative_ids.name` in the searchable fields, so customers can find products by any of their cross-reference codes.
- Improves search query normalisation via `website.searchable.mixin`: strips leading/trailing whitespace and collapses multiple spaces before the search is executed, reducing false "0 results" responses.
- Depends on `deltatech_alternative` for the underlying `alternative_ids` and `used_for` fields on `product.template`.
