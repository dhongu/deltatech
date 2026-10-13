# Confirmed bugs — integrated review 2026-10-03

## POSSTOCK-001 — P2: mixed-company template batches omit shared-product notifications

`models/product_template.py:32–34` collects nonempty product companies and applies that aggregate company set to all POS sessions. A batch containing a shared product and a company-B product therefore targets only company B, though company-A sessions also sell the shared product. Their stock badge remains stale after the shared quant changes. Compute eligible templates per destination configuration, allowing shared templates alongside matching company templates.

Evidence: actual `_notify_pos_stock_change()` executed with a mixed shared/company-B batch and two session companies; only B receives the notification. Source traced through quant write/create and native available-quantity update. Reproduction: `audit_coverage/reproductions/pos_warehouse_notifications.py`. No Odoo bus/database/browser scenario executed.

## Review limits

Read all source and traced native template quantity aggregation, POS field loader/warehouse context, tax-price options, bus callback registration and card template. Native price and websocket APIs match. Notifications read entire POS product payload under the originating environment; company-dependent taxes/costs and currency conversion need a separate multi-company database check before another defect is asserted. Existing browser tests were inspected only in relevant ranges, not executed. No measured test-line coverage.
