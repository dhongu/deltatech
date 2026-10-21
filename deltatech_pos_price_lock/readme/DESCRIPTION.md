Odoo lets you restrict price changes in the Point of Sale to managers. When every
employee working at the register is a manager, or when the business wants a fixed
price at the till whoever sells, that restriction is not enough: a manager can still
type any price on the order.

This module adds one more step to the standard restriction:

- **Managers included**: a new checkbox under *Price Control*, per register. When it is
  ticked, nobody can change the product price on the order — cashiers and managers
  alike.
- **Every manual path is closed**: the *Price* key of the numpad is disabled, and the
  price check of *Employees* (`pos_hr`) refuses the change with its usual message.
- **Prices still adapt by themselves**: prices recomputed by Odoo — pricelists, fiscal
  positions, taxes included in the price — keep working. Only the manual change is
  blocked.
- **Corrections go through the product**: a wrong price is fixed on the product form and
  reaches the register from there.

The lock is checked in the register screen. It does not verify the price of the orders
on the server.
