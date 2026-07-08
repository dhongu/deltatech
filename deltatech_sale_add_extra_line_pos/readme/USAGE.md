This module extends `deltatech_sale_add_extra_line` (where the **Extra Product** / **Extra %** / **Extra Qty** fields are configured on the product template) to also work in the Point of Sale.

1. Configure a product's **Extra Product** and **Extra Qty** multiplier as usual on the product template (see `deltatech_sale_add_extra_line`).
2. In a POS session, when the cashier adds that product to the cart, the configured extra product is added automatically as a separate order line — no manual step required.
3. If several products in the cart reference the same extra product, the extra quantities are summed and shown as a single consolidated line (`Extra Qty = Σ(main product qty × its multiplier)`).
4. Changing the quantity of a main product in the cart recalculates the extra line's quantity immediately.
5. When the POS session is closed, the extra lines are synced to the backend order like any other order line.
