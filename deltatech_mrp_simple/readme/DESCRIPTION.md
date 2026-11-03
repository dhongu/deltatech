Records a simple production without a bill of materials: you list the
components consumed and the products obtained, and the module moves the stock
and values the products obtained at the cost of the components.

**Simple production document.** In **Inventory > Operations > Simple
Production**, a document lists the products to consume (*Consume*) and the
products obtained (*Receipt*), with their quantities and units. **Add lines**
adds several components at once, with the same quantity.

**Two transfers.** **Confirm** creates a consumption transfer and a receipt
transfer, with the operation types chosen on the document (*Picking type
consume* and *Picking type receipt*). Each is validated automatically when its
option (*Validation consume*, *Validation receipt*) is ticked, otherwise it stays
to be validated by hand. Both transfers open from the **Consume** and **Receipt**
smart buttons. A document can be confirmed only once.

**Cost of the products obtained.** The cost of the consumed components (their
cost price times quantity) is split over the products obtained, in proportion
to their standard value (cost price times quantity), or to their quantity when
none has a cost price. **Recompute prices** redoes the split; the *Unit Price*
of a product obtained can also be changed by hand. This price is set on the
receipt moves.

**Zero cost check.** A product obtained with a unit price of 0 blocks the
confirmation, unless the system parameter `deltatech_mrp_simple.allow_zero_cost`
is set to `1` (**Settings > Technical > System Parameters**, developer mode).

**Product and sale order for the result.** Users in the group *Sale simple
production* see the option *Create product & sale*. When it is ticked,
**Confirm** also:

- creates the final product (storable, unpublished) from *Final product name*,
  *Category for final product* and *Unit of Measure*, or updates the selected
  *Final Product*. Its cost is the cost of the components and its sales price
  the sum of their sales prices, both per unit of the final quantity;
- adds it as a product obtained;
- creates a quotation for the *Client*, with the client's payment terms and
  pricelist.

**Link with the sale order.** When a *Sale Order* is set on the document, or
created by it, the order shows the **MRP Simple** smart button, which opens the
simple production.

On installation, the administrator is the only member of the group *Sale simple
production*; add other users in **Settings > Users & Companies > Groups**.

## Limitations

- **Add lines** stays available after confirmation, although the lines of a
  confirmed document no longer change the transfers.
- In Odoo 20 the receipt is valued by the standard stock valuation (at the
  current cost of the product), not at the *Unit Price* computed by the
  document.
