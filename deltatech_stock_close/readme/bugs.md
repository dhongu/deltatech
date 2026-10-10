# Known bugs

Review date: 2026-10-10. Target version: Odoo 18.

## STC-001 — P1: An archived valuation layer also leaves Odoo's own stock valuation

- **Status:** Open. Found on 2026-10-10 while writing the Apps page.
- **Location:** `models/stock_valuation_layer.py` (`active = fields.Boolean(default=True)`).
- **Trigger:** Archive valuation layers to close them for the storage sheet.
- **Actual behavior / impact:** With an `active` field, every search and read_group on
  `stock.valuation.layer` skips the archived layers. `product.product._get_valuation_layer_groups()`
  (stock_account 18.0) is one of them, so `value_svl` and `quantity_svl` of the products, the
  valuation report and the average cost no longer count the archived layers; the FIFO candidates
  (layers with a remaining quantity) are skipped as well. Archiving the layers of a closed period
  changes the stock value of the products unless the archived layers net to zero for each product.
- **Evidence:** Source inspection of the module and of `stock_account/models/product.py` (Odoo 18.0).
- **Suggested fix:** As on 19.0, use a non-magic flag (e.g. `l10n_ro_valuation_active`) that only the
  storage sheet reads, instead of `active`.
- **Validation needed:** Archiving layers leaves `value_svl` and `quantity_svl` of the products
  unchanged.
- **Limitations:** The Apps page now warns about the effect.

## STC-002 — P3: No "close at date" action

- **Status:** Open.
- **Location:** the module (no wizard).
- **Actual behavior / impact:** The former description promised to "close stock operations as of a
  given date"; the layers have to be selected and archived by hand.
- **Suggested fix:** A wizard "Close until date".
