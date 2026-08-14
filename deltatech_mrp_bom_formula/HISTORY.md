# History

## 19.0.1.0.0

- Port from 18.0. The copied body of `mrp.bom.explode` follows the 19.0 core, where the component quantity is rounded
  through `uom.round()` instead of `float_round()`.

## 18.0.1.0.0

- Initial release.
- Formula Code on `product.attribute` and `product.attribute.value`, generated from the name and kept unique through a
  numeric suffix.
- Numeric Value on `product.attribute.value`, for measurable characteristics.
- Quantity Formula on `mrp.bom.line`, evaluated with `safe_eval` against the `attr` and `num` dictionaries built from
  the manufactured variant.
- `mrp.bom.explode` is overridden to use the formula result instead of `product_qty`. The body is copied from
  `mrp/models/mrp_bom.py`; only the quantity computation differs, so it has to be compared with the core implementation
  on every version upgrade. Bills without any formula fall back to `super()`.
- Formulas are smoke tested on save against the first value of each attribute line.
