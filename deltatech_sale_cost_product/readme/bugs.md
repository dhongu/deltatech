# Confirmed bugs — 2026-10-03

## SALECOST-001 — P2: cost ignores order company, line unit and order currency

Both cost sums in `models/sale_order.py:12–14,21–23` multiply standard_price by product_uom_qty directly. Cost is per product base UoM and company cost currency, while quantity is in line UoM and cost_of_goods displays in the order currency. No with_company(order.company_id) is applied either. One dozen at base-unit cost10 produces10 instead of120; a100 RON cost on a EUR order is displayed as100 EUR without conversion. Multi-company batches may use the active company's cost for another company's order. Normalize cost using the order company, line UoM and order currency/date, consistently in both paths.

Evidence: entire source traced against native sale_margin._compute_purchase_price (:21–36), which performs company, UoM and currency conversion. Source/arithmetic evidence only; order confirmation/recalculation database scenario unexecuted.

## SALECOST-002 — P2: visibility group does not protect the cost field

The cost_of_goods field (:7) has no groups restriction; only list-view fields restrict group_view_cost_on_sale. An otherwise authorized sale-order reader outside the group can retrieve costs via export/read/RPC because view groups do not enforce field access. Apply the intended group at field declaration or clarify that this is only a display preference.

Evidence: field/view/security declarations read; security group comment explicitly says members can see cost column. Source-supported confidentiality gap if that group is intended to govern cost access; non-group ORM/export test unexecuted. Normal sale-order ACLs/company rules still apply.

## Limits

Full eligible source read, native sale view IDs and confirmation state-write integration checked. Cost is a snapshot and later line changes do not automatically recalculate it; no persistence-policy defect asserted without a requirement. Server action deliberately targets all confirmed orders by method name, so lack of selected-ID filtering not reported separately. No database/access/UI tests executed.
