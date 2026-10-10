Before you start, make sure variants are enabled and you have the right access
(see *Configuration*).

**Step 1 — Set the formula codes on the attribute**

Go to *Inventory ‣ Configuration ‣ Attributes* and open an attribute that
influences consumption (for example *Width*).

- **Formula Code** (next to the display type) is the technical identifier under
  which the attribute is visible in formulas. It is generated from the name
  (e.g. `finish`, `width`), can be edited and is unique.
- On each attribute value, **Formula Code** is what the `attr` dictionary
  returns, and **Numeric Value** is what the `num` dictionary returns. Fill
  the numeric value only for measurable characteristics (width, length,
  thickness). The *Numeric Value* column is optional: show it from the column
  selector.

| Value | Formula Code | Numeric Value |
|---|---|---|
| 1000 mm | `a_1000_mm` | 1000 |
| 1250 mm | `a_1250_mm` | 1250 |

![Attribute with Formula Code and numeric values](https://apps.odoocdn.com/apps/assets/19.0/deltatech_mrp_bom_formula/bom_formula_attribute_code.png)

**Step 2 — Write the formula on the component line**

Go to *Manufacturing ‣ Products ‣ Bills of Materials* and open a bill of
materials defined on the product template. On the **Components** tab, show the
optional **Quantity Formula** column (or open the line and use the field below
*Apply on Variants*) and write the formula. One line now covers all variants.

![Bill of materials with Quantity Formula](https://apps.odoocdn.com/apps/assets/19.0/deltatech_mrp_bom_formula/bom_formula_bom_lines.png)

Three patterns cover most cases:

```python
num["width"] / 1000                                # proportional to a dimension
0.8 if attr["finish"] == "galvanized" else 0.1     # discrete value
qty * num["width"] / 1000                          # qty = base quantity of the line
```

Available in the formula:

| Name | Content |
|---|---|
| `attr` | attribute code → code of the selected value |
| `num` | attribute code → numeric value of the selected value |
| `qty` | quantity entered on the BoM line |
| `ceil`, `floor` | round up / round down |

The usual math functions `min`, `max`, `abs`, `round`, `int`, `float` are
also available.

**Step 3 — Save**

The formula is checked on save. A wrong expression, such as a reference to a
code that does not exist, is rejected immediately in the BoM editor, with the
code named in the message, not when the order is confirmed.

![Validation error for an invalid formula](https://apps.odoocdn.com/apps/assets/19.0/deltatech_mrp_bom_formula/bom_formula_invalid_error.png)

**Step 4 — Launch production**

Create a manufacturing order for a configured variant. When the BoM is
exploded (manufacturing order, kit, forecast), each component quantity is
calculated from the configuration of the manufactured product. For example, an
order for 3 pieces of the *Galvanized, 1250 mm* variant gives
`num["width"] / 1000` = 1.25 kg per piece, so **3.75 kg** of sheet metal, and
0.8 kg per piece, so **2.40 kg** of zinc. Rounding to the unit of measure is
done upwards, as in standard Odoo.

![Manufacturing order with calculated quantities](https://apps.odoocdn.com/apps/assets/19.0/deltatech_mrp_bom_formula/bom_formula_mo_quantities.png)

**Good to know**

- A line without a formula keeps its quantity.
- An attribute that the product does not carry has a neutral value: `False` in
  `attr`, `0.0` in `num`. A semi-finished product BoM can therefore use a
  characteristic of the finished product.
- On nested BoMs, the configuration of the root product stays available; only
  the values the intermediate product actually carries override it.
- The formula must return a non-negative number. It is evaluated in isolation
  and cannot read or change records.
- The quantity on the line stays relevant: use it as a base through `qty`; it
  is the applied quantity if the formula is cleared.
- Formulas apply to components only, not to operation times or by-products,
  and only to attribute values defined in the catalogue (not free custom
  values typed on a sales order line).
