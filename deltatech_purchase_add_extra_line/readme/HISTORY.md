## 19.0.1.4.0

- [FIX] changing the product of a main line no longer leaves the extra line of the old product on the RFQ (PURCHASEEXTRA-001): when the new product has another extra product, the old extra line is replaced by a new one, with the product, unit of measure, quantity and computed price of the new extra; when the new product has no extra, the old extra line is removed. This applies to the form as well as to `write()`, imports and XML-RPC
- [FIX] deleting a main line now also deletes its extra line when the product no longer has an extra configured
- [FIX] an extra line whose product has an extra of its own is no longer taken for a main line
- [IMP] the extra lines are marked with the technical field `is_extra_line`, so the pair no longer depends on the current product configuration; the migration marks the extra lines created by the previous versions
- [FIX] the order lines are synchronized after all the line commands of a save are applied, so a product change saved from the form does not create the new extra line twice

## 19.0.1.3.1

- Own module icon, instead of the generic gears it had.

## 19.0.1.3.0

- [FIX] `check_extra_product` now also runs on `write()` of `product_qty`, `product_id` or `price_unit`: previously it only ran on `create()` and on the form's live `onchange_order_line`, so a quantity change saved through an inline list edit, an import or an XML-RPC write left the extra line at its old quantity and price (ticket #9275)

## 19.0.1.2.0

- [IMP] Romanian translation (`i18n/ro.po`): the group **Extra Line** and the fields **Extra Product**, **Extra Percent**, **Extra Qty** are now translated into Romanian, instead of staying in English on a Romanian interface
- [IMP] the three configuration fields finally have tooltips, kept **identical** to the ones in `deltatech_sale_add_extra_line`: both modules declare the same fields on `product.template`, so with both installed the last one loaded wins — divergent wording would make the tooltip depend on the load order. They are therefore neutral as to the kind of document ("ordered")
- [DOC] consultant sheet (`readme/FISA_CONSULTANT.md`) with 6 screenshots generated from `tests/test_screenshots.py`, documenting the flow and three limitations to tell the customer: the mechanism only works before the order is confirmed, a zero percent leaves the vendor price in place, and the configuration is shared with the sale module

## 19.0.1.1.0

- [IMP] a unit price typed in on the extra line is kept: the price computed from the percent set on the main product is no longer written back over it. The quantity keeps following the main line. Deleting the extra line is the way back to the computed price — it is regenerated on the next change of the order lines
- [FIX] a manual price is recognized on every flow, not only in the purchase order form: the price set by the module is recorded in the technical field `extra_price_computed`, so lines changed through `write()`, an import or XML-RPC are detected as well
- [FIX] a vendor price recomputation (which rewrites `price_unit` and `technical_price_unit` together) is no longer mistaken for a manual price, so the extra line goes back to its computed price
