This module lets a bill of material compute the quantity of a component from the attribute
values of the manufactured variant, instead of repeating the same component on one line per
configuration.

Standard Odoo can only include or exclude a component line for a given set of attribute values
("Apply on Variants"). The quantity itself stays constant, which forces one line per combination
as soon as the consumption depends on the configuration. This module adds a quantity formula on
the component line, evaluated against the configuration of the product being manufactured.

- Features:
  - a **Formula Code** on attributes and attribute values, used as identifier in formulas
  - a **Numeric Value** on attribute values, for measurable characteristics such as a length
  - a **Quantity Formula** on the bill of material component line
  - formulas are validated when saved, not when the manufacturing order is created
  - on nested bills, the configuration of the root product stays available

Two dictionaries are available in a formula:

- `attr` maps an attribute code to the code of the selected value, for example
  `0.8 if attr["finish"] == "galvanized" else 0.0`
- `num` maps an attribute code to its numeric value, for example
  `num["width"] * num["height"] / 1000000`

The quantity of the line is available as `qty`, and `ceil` and `floor` are available besides the
usual mathematical builtins. A line without a formula keeps its quantity unchanged.
