## Searching by alternative code

1. Open the website shop (`/shop`) and type an alternative / cross-reference code in the search bar (e.g. `DIN933`).
2. The search engine now includes `alternative_ids.name` in its searchable fields, so any product whose alternative code matches the query will appear in the results.
3. The query is normalised before searching: extra whitespace is collapsed, so `DIN 933` and `DIN933` produce the same results.

## Product page display

1. Navigate to any product page on the shop.
2. If the product has alternative codes configured (`alternative_ids`), each non-hidden code is rendered as a hidden `<span itemprop="alternateName">` element. These are invisible to visitors but readable by search engines and the site search index.
3. If the product has a primary `alternative_code` and the visitor is logged in, an **"Alternative code"** label and value are shown below the product form.
4. If the `used_for` field is filled in (e.g. `"Ford Focus 2005-2011"`), a **"Used For"** section is displayed on the product page.

## Enabling / disabling the website snippets

Both the "Alternative code" block and the "Used For" block are optional website templates with `customize_show="True"`. To toggle them:

1. Go to **Website > Customize** (pencil icon) while browsing any product page.
2. In the customization panel, locate **Alternative code** or **Used For** and switch them on or off.

## Configuring alternative codes on a product

Alternative codes are managed in `deltatech_alternative`. To add or edit them:

1. Go to **Inventory > Products > Products** (or **Sales > Products**).
2. Open a product and locate the **Alternatives** tab (added by `deltatech_alternative`).
3. Add one or more alternative/cross-reference codes. These codes will immediately be searchable on the website.
