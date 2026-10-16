"Do you have it in the other shop?" — answered at the till, without calling the other shop.

This module extends `deltatech_pos_stock` with the stock of the **other shops** of the company,
loaded with the POS session.

- **On the product card**: under the quantity of this shop, the badge shows how much the other
  shops have together (`+12`). Negative stock in one shop does not reduce what another shop can
  hand over.
- **Filter in the product list**: *All products*, *In stock here*, *In other shops*. A second tap
  on the active filter takes it off. The filter stays reachable when the list is empty.
- **Product info popup**: the standard popup lists every warehouse of the company. It is limited
  to this shop and the chosen shops, so the central warehouse or a transit location does not show
  up as something the cashier can hand over.
- **Works offline**: the figures travel with the session. When the server cannot be reached, the
  product info button opens a popup with the stock per shop, built from the session data.
- **Kept up to date**: a sale, a receipt or a transfer in another shop is pushed to the open
  registers on the channel already used by `deltatech_pos_stock`.
- **One query**: the stock of all the shops is read with a single grouped query on the quants,
  not one query per shop.
- **Same figure as the badge**: on hand or available (on hand minus reservations), following the
  *Quantity shown* setting of `deltatech_pos_stock`.
