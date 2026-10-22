## 20.0.1.0.2 (2026-10-22)

- The price including taxes of the labels is computed by `deltatech_product_labels`, whose default
  layouts now print it too.

## 20.0.1.0.1 (2026-10-22)

- Migration to 20.0 (19.0.1.0.0 and 19.0.1.0.1): **Print Labels** button, layout **Shelf label
  with price** and the warehouse of the document proposed in the wizard.

## 19.0.1.0.1 (2026-10-22)

- New label layout **Shelf label with price**: product name, price including taxes, code and unit
  of measure. The labels layouts of `deltatech_product_labels` print no price, so the labels of a
  price change could not show the new price. It is proposed by default when the wizard is opened
  from a price change document.
- The wizard proposes the warehouse of the document; before, it proposed the main warehouse of the
  first company.
- Romanian translation.

## 19.0.1.0.0 (2026-10-22)

- Initial version: **Print Labels** button on the price change document, which opens the product
  labels wizard with the products of the document.
