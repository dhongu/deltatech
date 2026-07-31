## 19.0.1.1.0

- [IMP] a unit price typed in on the extra line is kept: the price computed from the percent set on the main product is no longer written back over it. The quantity keeps following the main line. Deleting the extra line is the way back to the computed price — it is regenerated on the next change of the order lines
- [FIX] a manual price is recognized on every flow, not only in the purchase order form: the price set by the module is recorded in the technical field `extra_price_computed`, so lines changed through `write()`, an import or XML-RPC are detected as well
- [FIX] a vendor price recomputation (which rewrites `price_unit` and `technical_price_unit` together) is no longer mistaken for a manual price, so the extra line goes back to its computed price
