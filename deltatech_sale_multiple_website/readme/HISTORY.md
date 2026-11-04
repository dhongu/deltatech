## 20.0.1.1.3 (2026-11-04)

- Migration to Odoo 20.0: the product page restrictions follow the new `ProductPage`
  interaction, the combination info hook is `_get_additional_combination_info`, and
  "Website Check Quantity" is edited on the variant form (the variant easy-edit form no
  longer exists in Odoo 20).

## 19.0.1.1.3 (2026-10-18)

- Fix "Could not destroy interaction QuantityInfoPopover" when entering the website editor
  after changing a variant: the cleanup disposed a popover already replaced on combination
  change.

## 19.0.1.1.2 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.1.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
