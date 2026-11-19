## Limitations

The secondary quantity is an input and information helper on the line. The
document itself stays in the line unit (usually the product base unit), so the
alternative unit does not reach:

- **Prices.** The unit price stays per line unit. A vendor price of 120 per
  bar of 6 m must be entered as 20 per m, and the vendor pricelist cannot be
  expressed in bars. When the factor does not divide the price exactly
  (125 / 6 = 20.8333), the vendor bill and the received e-Invoice (in bars)
  can differ by rounding.
- **Received quantity.** On the receipt, the secondary column shows the
  demand, computed from the ordered quantity, not the quantity actually
  received. A short delivery of 8 bars out of 10 is entered as 48 m. Detailed
  operations and the Barcode app have no secondary unit.
- **Stock.** Stock and stock reports are only in the base unit; the quantity
  on hand is never shown in bars.
- **Manufacturing.** The module does not depend on `mrp`: bills of materials
  and manufacturing orders have no secondary unit, and the consumption is in
  the base unit. Cutting, offcuts and bar remnants are not handled.
- **Rounding.** A quantity entered in the secondary unit is rounded **up** to
  a whole base unit. This fits pieces, not metres or kilograms: with
  1 bar = 5.8 m, 3 bars become 18 m instead of 17.4 m, and the line then shows
  3.103 bars.

## Do not use the alternative unit as the line unit

The conversion factor lives only in this module. If the generic unit (e.g.
“Bar”) is added to the product packagings, to a bill of materials line or to
a vendor pricelist line, Odoo converts it with the **global** factor of the
unit, not with the product factor, and no error is raised.

## When the bar must be a real unit

When the price, the receipt or the bill of materials must be in the
alternative unit, use a real unit of measure per factor instead of this
module, with standard Odoo:

1. Create one unit per distinct factor, with the base unit as reference unit:
   “Bar 6 m” (reference unit `m`, ratio 6), “Bar 5 m” (reference unit `m`,
   ratio 5). Products with the same bar length share the same unit.
2. Add the unit to the *Packagings* of each product (`uom_ids`).
3. Map the UNECE code of each such unit (`deltatech_uom_unece`), otherwise
   e-Invoicing declares `C62` (piece).
4. To keep the order unit on receipts and deliveries, enable the system
   parameter `stock.propagate_uom`; it applies to all products.

Overriding `uom.uom._compute_quantity` with the product in the context is not
enough to obtain the same result: stock valuation at receipt
(`purchase_stock`), the purchase price, the sale, purchase and invoice SQL
reports and the product catalog in JS use `uom.factor` directly.

Generating these units automatically from the product factor lines is a
possible future evolution of this module.
