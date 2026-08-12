## 19.0.1.4.0

- [IMP] the product of the extra line goes through a hook, `SaleOrderLine._get_extra_product()`, instead of being read from `product_id.extra_product_id` in place. A module can now decide the extra product from the order line, so the line no longer requires the field to be filled in on every product. The default behaviour is unchanged

## 19.0.1.3.1

- [FIX] the field tooltips are now IDENTICAL to the ones in `deltatech_purchase_add_extra_line`: both modules declare the same three fields on `product.template`, so with both installed the last one loaded wins and divergent wording made the tooltip depend on the load order. They are neutral as to the kind of document ("ordered") and mention both the price list and the vendor price

## 19.0.1.3.0

- [IMP] Romanian translation (`i18n/ro.po`): the group reads **Linie suplimentară** and the fields **Produs suplimentar**, **Procent suplimentar**, **Cantitate suplimentară**, instead of staying in English on a Romanian interface
- [IMP] the field tooltips describe the current behaviour: the percent tooltip no longer claims that a zero percent uses the price of the extra product "directly" (since 19.0.1.1.0 the standard price computation applies, with the pricelist, currency and unit of measure of the order), and the quantity tooltip states that the value is a multiplier of the main line quantity

## 19.0.1.2.0

- [FIX] the e-commerce cart generates the extra line again: the module hooked on `_cart_update`, a method that no longer exists in the `website_sale` of Odoo 19 (replaced by `_cart_add` and `_cart_update_line_quantity`), so the override was dead code and orders placed from the shop got no extra line. The `_verify_cart_after_update` hook, called after both cart methods, is used instead
- [IMP] tests on the cart flow: the extra line is created when the main product is added, its quantity follows a quantity change (including the `Extra Qty` multiplier), a price typed in on it is kept, and it is removed together with the main line

## 19.0.1.1.1

- [FIX] the test on the currency of the extra line no longer assumes the company is not in the currency of the test pricelist: it builds its own currency, so no conversion is silently skipped

## 19.0.1.1.0

- [IMP] a unit price typed in on the extra line is kept: the price computed from the main line (percent or list price) is no longer written back over it. The quantity keeps following the main line. Deleting the extra line is the way back to the computed price — it is regenerated on the next change of the order lines
- [FIX] a manual price is recognized on every flow, not only in the sale order form: the price set by the module is recorded in the technical field `extra_price_computed`, so lines changed through `write()`, an import, XML-RPC or the website checkout are detected as well
- [FIX] a pricelist recomputation (which rewrites `price_unit` and `technical_price_unit` together) is no longer mistaken for a manual price, so the extra line goes back to its computed price
- [FIX] with a zero percent, the price of the extra line no longer comes from `lst_price` (the list price of the product, in the currency of the company): the standard price computation applies instead, so the pricelist, the currency of the order and the unit of measure are taken into account
