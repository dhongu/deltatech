## 19.0.1.2.0 (2026-10-22)

- Migration to 19.0.
- New log of the list price changes (`product.price.change.log`): one line for each product and
  day, from the price of the previous day to the current price; a change back to the previous price
  removes the line. Shown in *Sales > Products > List Price Changes* and on the product form.
- New document type *From price changes*, with the **Load Price Changes** button: brings in the
  logged changes not yet taken by another document, so the price change minutes can be printed
  after the prices were changed directly on the products.
- The prices written by a confirmed *In product* document are not logged again.
- The report shows the prices including taxes, the totals and the signatures, and the change date
  for the documents made from the log.
- The document gets its number at confirmation for all types; before, only the *In pricelist*
  documents were numbered and the others stayed `/`.
- The price change report of a variant listed the lines of the template with the same id as the
  variant; it now lists the lines of the variant.
- Salespersons can read the price change documents; before, only the sales managers had access.
