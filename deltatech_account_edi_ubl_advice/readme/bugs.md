# Bug review — UBL Despatch Advice

Review date: 2026-10-02. Target version: Odoo 19.

## UBLADVICE-001 — P1: Sales-only UBL export reaches undeclared stock dependencies

- **Status:** Open.
- **Location:** models/account_edi_ubl.py, _add_invoice_header_nodes(); __manifest__.py.
- **Trigger:** Install the addon with account_edi_ubl_cii and sale, without sale_stock/stock, then export a customer invoice through UBL BIS3.
- **Actual behavior:** The only optional dependency guard checks sale_line_ids. That field exists with sale alone. The method then accesses env['stock.picking'] and sale_line.move_ids, supplied by stock and sale_stock respectively. The manifest declares neither. The header export therefore fails on an otherwise valid sales-only installation.
- **Evidence:** Native sale/models/account_move_line.py declares sale_line_ids; sale_stock/models/sale_order_line.py declares move_ids. Addon source checks only the former before unconditionally accessing the stock model. Manifest depends only on account_edi_ubl_cii. No database export executed.
- **Impact:** Customer invoice UBL generation fails when stock integration is absent, instead of simply omitting despatch references.
- **Suggested fix:** Declare sale_stock if stock references are mandatory, or guard both the model and move field and skip the extension when stock integration is absent.
- **Validation needed:** Sale-only and sale_stock installations, customer/vendor invoices, no linked sale lines and completed shipments.

## Review limitations

All eligible source read and native dependency providers compared. No Odoo install, UBL schema/export or database integration tests executed.
