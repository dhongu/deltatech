# Confirmed bugs — 2026-10-03

## CATCOLOR-001 — P2: picking category cache lacks dependencies

categ_ids is nonstored compute without @api.depends, while reading move_line_ids.product_id.categ_id. Once cached, adding/removing detailed operations or changing their product/category does not invalidate it through native ORM triggers. Declare complete dependencies so category tags reflect the current detailed operations within the Environment. Fresh requests can mask stale values.

Evidence: all source, native category form/stock kanban state anchors and previously traced get_depends/modified contracts read. Source-only, no database/kanban test executed.

## Limits

Uses detailed move lines rather than planned moves deliberately; no tags on unreserved demand not separately reported. Color range 1–11 matches ordinary palette indices. No database/view/browser tests or fixes.
