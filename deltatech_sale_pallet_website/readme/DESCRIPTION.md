Products sold in bulk, such as bricks or tiles, are delivered on pallets that
the customer pays for. The `deltatech_sale_pallet` module adds the pallet
lines on backend sales orders; this module brings the same logic to the
eCommerce shop, so the pallets are shown on the product page and added to the
cart automatically.

**Pallet price on the product page.** For products with a minimum pallet
quantity, the product page shows a line such as *When buying 10 units, the
price is ...*, where the price is the minimum pallet quantity at the sales
price plus the price of the pallet product.

**Pallet lines in the cart.** Each time a product is added to the cart or its
quantity is changed, the pallet lines are recalculated: one line per pallet
product, with the number of full pallets needed by all the cart lines that
use that pallet. A quantity below one full pallet adds no pallet. When the
last product that needs a pallet is removed from the cart, its pallet line is
removed too.

**Delivery price includes the pallets.** The pallet lines are updated before
the delivery price and the cart quantity are recalculated, so both take the
pallets into account.

## Configuration

On the product form, in the *Inventory* tab, the **Palletizing** section
(from `deltatech_sale_pallet`) holds the settings used by the shop:

- **Pallet Product**: the product that represents the pallet, sold at its own
  sales price;
- **Pallet Qty Min**: the quantity that fills one pallet.

Products without a pallet product and a minimum quantity are sold in the shop
as usual. The **Pallet** flag on product categories is not used by the shop.
