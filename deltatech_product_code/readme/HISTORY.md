# 19.0.1.1.1 (2026-10-09)

- Apps Store banner (banner.json).

# 19.0.1.1.0 (2026-10-07)

- Barcodes from the GS1 company prefix: on the product category, "Barcode Source" = "GS1 company prefix" allocates to each new product the next free GTIN-13 in the range of the prefix received from GS1 (prefix + item reference + check digit). Product and packaging barcodes, including archived ones, are taken into account; the category shows how many codes are still free, and an error is raised when the range is used up.
- The default internal barcode prefix of new categories is now 20 (GS1 range for internal use) instead of 40, which belongs to GS1 Germany. Existing categories keep their prefix.

# 19.0.1.0.8 (2026-10-02)

- Fix the "Find Duplicate" action on product variants: it referenced a non-existent action (`product.product_open_variants`) and the SQL looked for `company_id` in `product_product` (the company is read from the template). Queries moved to `SQL()` and the models are flushed before the search; regression test added.

# 19.0.1.0.7

- Own module icon, instead of the generic gears it had.

# Changelog

## 19.0.1.0.6 (2026-09-25)

- Fix: the category sequence could propose an internal reference that was
  already used. Its counter does not know about codes created outside the
  sequence (catalog imports, supplier invoice imports, mass renumbering,
  manually typed codes), so "New internal code" and automatic coding on
  product creation failed with "Internal Reference already exists". When the
  proposed code is taken (including by archived products or other companies),
  the sequence is now moved past the highest number already used with its
  prefix/suffix and the next number is taken. Sequences with date ranges are
  not synchronised. Ported from a customer project.
