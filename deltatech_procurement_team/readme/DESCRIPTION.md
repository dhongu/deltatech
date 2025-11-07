Deltatech Procurement Team

Purpose
- This module ensures that Purchase Orders (RFQs) generated from Sales Orders are split per Sales Team when they target the same vendor. It enables reporting, filtering, and approval flows per team while keeping the standard procurement flow intact.

Features
- Propagates `team_id` from Sales Order to procurement and then to Purchase Orders.
- Extends PO grouping domain so procurements from different Sales Teams never merge into a single PO.
- Stores `team_id` on `purchase.order` for visibility and analysis.
- Works with Buy + MTO and MTS else MTO flows; compatible with orderpoints (reordering rules).
- No impact on replenishments not originating from Sales Orders (those typically have no team and keep default grouping).

How it works
- `sale.order.line._prepare_procurement_values` injects the order's `team_id` into procurement values.
- `procurement.group` keeps team as a grouping key so similar procurements are aggregated within the same team.
- `stock.rule` customizations:
  - `_make_po_get_domain` adds `('team_id', '=', team_id)` when available to split PO per team.
  - `_prepare_purchase_order` sets `team_id` on PO creation values.
- `purchase.order` gains a `team_id` field.

Configuration
- Ensure your sellable products have a vendor and appropriate routes (e.g., Buy + MTO or MTS else MTO).
- Optional: create reordering rules if you also want planning via orderpoints.
- Install the module and (optionally) add `team_id` to PO list/form views using Studio or a custom view for filtering/reporting.

Usage
- Create Sales Orders assigned to different Sales Teams using products from the same vendor.
- Confirm the orders and run the scheduler; the system will create one draft RFQ per team for that vendor.

Compatibility
- Odoo 18. Depends on `sales_team`, `stock`, `sale_stock`, `purchase`, `purchase_stock`.
- Multi-company aware; POs are always created in the correct company.

Testing
- Includes a test that creates 4 SOs (2 per team) for the same vendor and verifies that exactly 2 RFQs are created (one per team), with aggregated quantities.

Maintainer
- Deltatech / Terrabit — Dorin Hongu


