# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## STOCKDELIVERY-001 — P3: Invoice delivery lookup requires undeclared stock-integration dependencies

- **Status:** Fixed in 19.0.1.0.2 — `sale_stock` and `purchase_stock` added to `depends` in `__manifest__.py`.
- **Priority note:** Lowered from P1 to P3. `stock_account`, `sale_stock` and `purchase_stock` are `auto_install` and are installed automatically with `account` + `stock` + `sale` + `purchase`, so the error only occurs if a bridge was uninstalled manually. Declaring them installs nothing new in existing databases: every database with this addon already has both bridges (and `purchase` was already a dependency). Defensive field checks were not chosen because the button has no meaning without the stock moves.
- **Location:** __manifest__.py; models/account_invoice.py, invoice_print_delivery().
- **Trigger:** Install this addon and its declared dependencies in a minimal database, then use the invoice button to open related deliveries/receptions.
- **Actual behavior:** The method unconditionally accesses sale_line.move_ids and purchase_line.move_ids. Those fields are provided by sale_stock and purchase_stock, while the manifest declares sale, purchase, stock, and account only. Without the integration addon, the matching invoice line branch raises AttributeError.
- **Evidence:** Inspected the manifest and local field providers: sale_stock/models/sale_order_line.py and purchase_stock/models/purchase_order_line.py. Sale and purchase manifests do not depend on their stock integration modules. No fresh database installation was run.
- **Impact:** The installed invoice button fails in a supported minimal dependency installation.
- **Suggested fix:** Declare sale_stock and purchase_stock as runtime dependencies, or conditionally support the integrations without reading absent fields.
- **Validation needed:** Fresh installation with declared dependencies only, sale-linked invoice, purchase-linked bill, multiple deliveries, and invoices without stock documents.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. STOCKDELIVERY-001 was fixed on 2026-10-01.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **STOCKDELIVERY-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.
