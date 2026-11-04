Extends sale quantity multiples to eCommerce. Product minimum and multiple
quantities can be enforced only for website carts or globally, and the active
restrictions are displayed on product and cart pages.

Cart quantities are normalized before Odoo checks stock. If stock availability
caps a request, the cart falls back to the greatest available quantity that still
satisfies both rules. Variant changes refresh the displayed restrictions.
