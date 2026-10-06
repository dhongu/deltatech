By default, Odoo lets a transfer be validated even when the stock is not there, and the
quantity on hand quietly goes below zero. The error surfaces weeks later, at the next
inventory count. This module stops the move at validation instead, and tells the user
what is actually left in the location.

- **Blocks negative stock at validation**: A transfer that would take an internal
  location below zero cannot be validated.
- **Clear message**: The user sees the product, the location and the quantity that
  would remain, and is pointed to adjust the quantities or correct the stock.
- **Exceptions per location**: Allow negative stock on the locations where you need
  it, such as a production floor or a consignment area.
- **Checked per lot, package and owner**: The quantity available in the location is
  checked for the exact lot, package and owner being moved.
- **Company setting**: Turn the rule on or off separately for each company.
