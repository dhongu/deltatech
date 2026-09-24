## 19.0.2.10.0 (2026-09-24)

- **The inventory price no longer revalues the existing stock.** Until now, validating an inventory
  wrote the line *Price* into the product cost with a context key that no longer exists in 19.0
  (`disable_auto_svl`). On average cost products, and on standard cost products on lines with no
  theoretical quantity, this created a `product.value`, i.e. it revalued the whole stock of the
  product, in all locations. Now the product cost is not rewritten: only the surplus of the count
  enters at the line price (the value of the inventory move is difference × line price), and the
  average cost is recomputed as a weighted average. On FIFO the new layer enters at the line price;
  missing quantities still leave at the current cost. On standard cost the line price becomes the
  standard cost only on a line with no theoretical quantity, and only if the product has no valued
  stock in the company.
- The `stock.use_inventory_price` parameter now always decides: when it is off, the line price is
  ignored, including on the lines with no theoretical quantity.
- A **negative counted quantity** raises the explanatory message again, instead of a server error
  (`TypeError`).
- **Include Exhausted Products** works again when *Products* is left empty: the product filter used
  the product type `product`, which no longer exists in 19.0.
- The inventory moves, and therefore the accounting entries, carry the **inventory document name** as
  reference, instead of *Product Quantity Updated (user)*.
- **Inventory Diff** report: on a document with several locations, the missing quantities are no
  longer repeated under every location. The quantity difference keeps its decimals (it was rounded to
  an integer) and the numeric columns are right-aligned again (`text-end`).
- The **Merge** wizard proposes the current date, not the date the server was started.
- The chatter message of **Confirm Stock** shows the location again (broken placeholder).
- Romanian translations completed; the group *Can update quantities* is now translated as such.

## 19.0.2.9.0 (2026-09-14)

- **Grouping** is available again in the product replenishment wizard (*product.replenish*). The
  field existed in 18.0 as `group_id` (`procurement.group`) and was dropped in the 19.0 port because
  the `procurement.group` model no longer exists in core; it is now based on the new O19 mechanism,
  `stock.reference` (`reference_ids` on `stock.move`).
- The grouping is filled in **automatically, once per day and per warehouse**: all replenishments
  launched on the same day from the same warehouse get the same reference and end up on a single
  `stock.picking`, instead of one document per product. The field stays editable for a different
  manual grouping.
- The anti-duplicate guard is kept, but it now works per product and reference (not per reference,
  as it did per group in 18.0); otherwise the automatic daily grouping would block the replenishment
  of the second product on the same day.

## 19.0.2.8.0 (2026-09-10)

- **Valuation snapshot on the inventory line.** The line now carries the unit valuation cost
  (*Unit Value*), the value of the on hand and counted quantities, the estimated difference value and
  the value actually posted at validation (*Posted Value*), with the four totals summed on the
  document. Until now the document showed only quantities and an editable price, so the money impact
  of a count could not be seen anywhere — neither before validating it, nor afterwards.
- The inventory move keeps an **Inventory Line** link (`stock.move.inventory_line_id`), which is how
  the posted value is read back per line.
- All the new fields are restricted to `stock.group_stock_manager`, like the standard valuation
  fields on quants, so warehouse operators keep counting without seeing values.
- Lines created before this version keep an empty *Unit Value*, so their values stay at zero: the
  snapshot is taken when the line is generated and is not reconstructed retroactively.

## 19.0.2.7.5 (2026-09-10)

- Applying an inventory adjustment through the standard *Apply* flow no longer crashes: the counting
  date sent by `stock.inventory.adjustment.name` is accepted and now also dates the generated
  inventory document, not only its moves.

## 19.0.2.7.4 (2026-08-22)

- The **delete guard** on inventory adjustments is active again: only adjustments
  in *Draft* or *Cancelled* state can be deleted. An adjustment that is *In
  Progress* or *Validated* has already generated stock moves, and deleting it
  left those moves behind without their source document. The guard existed in
  18.0 but had been commented out during the 19.0 port, so any adjustment could
  be deleted regardless of its state — silently, with no warning.
- The two documented exceptions are preserved: module uninstall
  (`_force_unlink`) and the explicit merge of adjustments, which deletes the
  merged (validated) documents with `merge_inventory=True` in the context after
  moving their lines and stock moves to the resulting adjustment.

## 19.0.2.7.3 (2026-08-15)

- Imp: `stock.inventory.line.partner_id` is now indexed — a foreign key to `res_partner` on a table that grows with every stock count.
  Context: `res_partner` is referenced by ~158 foreign-key columns; on a production database 77 of them had no index, so a single partner deletion triggered sequential scans over 3.180 MB of tables. Deleting 5.350 merged partner records took over 8 minutes without indexes and 190 seconds with them, foreign keys left ENABLED.

## 19.0.2.7.2 (2026-08-05)

- **Inventory Note** is again carried over to the generated stock move, so the
  reason of a quantity update stays visible in the product move history. The
  18.0 code wrote it to `name`, but in 19.0 the standard no longer returns a
  `name` key in `_get_inventory_move_values` — it uses `inventory_name`, which
  feeds `stock.move.reference` for inventory moves. The line had been commented
  out during a 19.0 cleanup, which silently dropped the per-line reason: the
  note could be filled in, but was stored nowhere permanent.
- The note is cleared when the adjustment is applied, so it is not silently
  reused as the reason of a later adjustment on the same quant (the standard
  `action_clear_inventory_quantity` does not reset custom fields).

## 19.0.2.7.1 (2026-08-04)

- The **Inventory Note** column in the inventory adjustment list is now shown by
  default (`optional="show"` instead of `optional="hide"`). Users had to enable
  it manually from the optional-columns menu to record why a quantity was
  changed, so in practice the reason was almost never filled in. The note is
  used as the name of the generated stock move, which makes it the only
  per-line trace of the reason in the product move history.
