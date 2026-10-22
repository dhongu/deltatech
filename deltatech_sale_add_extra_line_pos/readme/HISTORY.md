## 19.0.1.0.5 (2026-10-22)

- Listed on Odoo Apps as *POS Auto Extra Lines* (was *POS Add Extra Line*). The technical name `deltatech_sale_add_extra_line_pos` does not change.

## 19.0.1.0.4

- [FIX] POSEXTRA-001: no extra line is added when the main product is not
  added (configurator, lot or weight popup cancelled, refund constraint).
- [FIX] POSEXTRA-002: removing a main line updates its extra line, and removes
  it when no other line asks for that extra product.
- [FIX] POSEXTRA-003: the first extra line takes its quantity from the lines
  the order actually holds (weighed, negative in a return preset, merged with
  an existing line), not from the requested quantity.
- Tests: POS tours for the three cases.

## 19.0.1.0.3

- Tests: a POS tour checks that the extra line is added with the configured
  quantity multiplier and follows the main line quantity; the previous test
  class had no test method, so nothing ran.

## 19.0.1.0.2

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.1

- [FIX] the extra line is added again in the POS. Since 19.0 the point of sale
  builds a line from `vals.product_tmpl_id` and no longer from `vals.product_id`,
  so the patch read an undefined product and silently skipped the extra line -
  the SGR deposit product was never added to the receipt. The template is now
  read from either key, and the extra line is requested with the template as
  well, which 19.0 requires
