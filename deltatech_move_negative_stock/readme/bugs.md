# Known bugs

Review date: 2026-10-08. Target version: Odoo 18.

## NEG-001 — P1: The daily cron reads a location manager field that does not exist on 18.0

- **Status:** Open on 18.0. Fixed on 19.0, where the module defines `stock.location.user_id` ("Manager") and skips locations without one.
- **Location:** `models/stock_location.py`, `send_mail_negative_stock()`, line 28; `data/mail_data.xml` (`partner_to`, `lang` and the body use `object.user_id`).
- **Trigger:** The "Send negative stock" cron runs while an internal location holds a negative quant.
- **Actual behavior / impact:** `self.user_id` is read on `stock.location`, but neither Odoo 18 nor this module defines that field. The cron raises `AttributeError` on the first location with negative stock, so no notification is ever sent, and the cron fails every day. The feature described on the Apps page does not work on 18.0.
- **Evidence:** `stock.location` in `odoo/addons/stock/models/stock_location.py` (branch 18.0) has no `user_id`; the module only inherits the model and adds no field. The 19.0 port (`0356b8ba7`) adds the field.
- **Suggested fix:** Backport the 19.0 model: add `user_id = fields.Many2one("res.users", string="Manager")` on `stock.location`, show it on the location form, and return early when it is empty.
- **Validation needed:** Create a negative quant in an internal location with and without a manager, run the cron, check that one email is sent to the manager and that the cron finishes without error.
- **Limitations:** Verified by source inspection only; the cron was not run on an 18.0 database.

## NEG-002 — P2: Negative quantities are not summed per product

- **Status:** Open on 18.0. Fixed on 19.0 (`get_negative_products()` returns a dict keyed by product).
- **Location:** `models/stock_location.py`, `get_negative_products()`, lines 16–23.
- **Trigger:** The same product is negative in two or more sub-locations of the location.
- **Actual behavior / impact:** `products_dict` is a list of one-item dicts, so `quant.product_id in products_dict` never matches and the `+=` branch is never reached. The email lists the product once per quant instead of once with the total.
- **Evidence:** Source inspection; the list membership test compares a product record with dicts.
- **Suggested fix:** Backport the 19.0 implementation (a dict `{product: total}`) and adapt the template loop, as on 19.0.
- **Validation needed:** Two negative quants of the same product in two sub-locations produce a single line with the sum.
- **Limitations:** Only reachable once NEG-001 is fixed.
