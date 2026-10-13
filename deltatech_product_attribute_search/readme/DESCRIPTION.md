On a product with variants, what tells two variants apart on screen is the attribute
values in their name — `Apples (Gala Mast, 70/75 mm)`. Standard Odoo, however, searches
only the template name, the internal reference and the barcode. Typing the variety or
the size into a product field on a sales or purchase order line therefore returns
nothing, and the operator has to open **Search more…** and scroll a list ordered by
database id.

This module makes the values searchable, on every product field and in every search view.

Key business benefits:

- **Fewer wrong lines.** The operator finds the variant by the words printed on the
  goods — variety, size, grade — instead of picking from a list where only the position
  differs.
- **Same list in sales and purchasing.** A variant found by attribute is found the same
  way wherever the product field appears, so the two departments stop seeing different
  results for the same query.
- **Words can be mixed.** Every word typed has to match somewhere — the name, the
  reference or one of the values — so `apples gala 80` narrows down in one go, without
  any single field holding all three words.
- **Noisy attributes can be left out.** An attribute whose values are too generic to
  search on (a grade named `1/5`, a colour named `2`) can be excluded, so it does not
  flood the results.
- **No cost on searches that already worked.** Standard Odoo answers first; the extra
  lookup runs only when it left the page unfilled.
