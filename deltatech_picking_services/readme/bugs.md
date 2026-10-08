# Confirmed bugs — 2026-10-03

## PICKSERVICE-001 — P1: service lines bypass parent picking company access

**Status:** Fixed in 19.0.1.0.2. Stored `company_id` related to
`picking_id.company_id` and record rule `picking_service_line_rule`
(`company_ids`); `picking_id` is now `ondelete="cascade"`. Covered by
`test_service_line_company_isolation` and `test_service_lines_deleted_with_picking`.

`security/ir.model.access.csv:2` grants stock users all CRUD on `picking.service.line`. The model has no company rule, company field or explicit parent-access enforcement. Native stock.picking company rules restrict only pickings; a Many2one link does not inherit their access rules. A stock user can directly search/read line product, description, quantity and price or write/unlink lines belonging to pickings from an inaccessible company. Apply rules following the parent picking company and enforce appropriate parent access for mutation.

Evidence: complete source/ACL inspection and repository search for model/rule references; native stock_picking_rule examined. Source-supported access gap; direct multi-company ORM CRUD reproduction remains unexecuted. Reading the related picking separately may still fail, which does not protect the line's own scalar fields.

## Limits

Entire eligible source reviewed; native product allowed-UoM fields and stock picking operations page anchors checked. Subtotals are simple quantity×price as implemented; no invoicing behavior is provided. picking_id is optional and has no cascade, so orphan lifecycle requires follow-up validation; not added as another confirmed bug here. No database/view tests executed.
