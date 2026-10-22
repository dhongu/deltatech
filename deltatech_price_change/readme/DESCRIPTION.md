Controls the changes of the products' sale price, with a dated and numbered price change document
and its report (the price change minutes).

**Log of list price changes**

- Every change of the list price of a product (by hand, by import or by another module) is logged
  in *Sales > Products > List Price Changes* and on the product form (**Price History** button).
- One log line is kept for each product and day: the old price is the price before the first
  change of the day, the new price is the current one. If the price comes back to the price of the
  previous day, the log line is removed.
- A log line already taken in a confirmed document is not changed any more; a new change on the
  same day starts a new log line.

**Price change document**

- Type *From price changes*: the **Load Price Changes** button brings in the logged changes up to
  the document date that are not in another document, one line for each product and day, with the
  stock quantity and the old, new and difference amounts. The confirmation does not write any
  price, the prices are already changed.
- Type *In product*: the new prices are written in the products at confirmation.
- Type *In pricelist*: the new prices are written as fixed prices in the pricelists at
  confirmation.
- At confirmation, a document without a location is split into one document for each internal
  location with stock of its products.
- The report shows the prices with and without taxes, the amounts and the signatures.

The labels of the changed products can be printed from the document with
`deltatech_price_change_label`, which installs by itself together with `deltatech_product_labels`.

Can print price changes from product template. If a system parameter is set -
price_change.public_pricelist_id - with the id of a pricelist, only the lines related to that
pricelist will be printed.
