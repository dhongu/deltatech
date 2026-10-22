Adds the Point of Sale orders that were not invoiced to the sale margin report
(*Raport analiză profit*) of `deltatech_sale_margin`. The invoiced orders are
already in the report through their invoice, so they are not counted twice.

For each order line the report shows:

- the sale value without VAT, in the company currency; returns are negative;
- the cost of the line, as computed by the Point of Sale when the session is closed,
  or the current product cost while the session is still open;
- the salesperson of the order and the sales journal of the point of sale; with
  `deltatech_sale_commission`, the commission rates set on that journal give the
  computed commission;
- the order itself, with a *POS Sales* filter and a grouping by order.

The rows of the orders are read-only: the real commission, *Commission Paid* and the
purchase price are kept on the invoice lines only, and the commission and cost wizards
leave the orders out.

The module is not installed automatically: it changes the figures of the report.
