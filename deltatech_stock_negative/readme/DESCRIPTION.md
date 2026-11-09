By default, Odoo lets a transfer be validated even when the stock is not there, and the
quantity on hand quietly goes below zero. The error surfaces weeks later, at the next
inventory count. This module stops the move at validation instead, and tells the user
what is actually left in the location.

- **Blocks negative stock at validation**: A transfer that would take an internal
  location below zero cannot be validated.
- **Clear message**: The user sees the product, the location and the quantity that
  would remain, and is pointed to adjust the quantities or correct the stock.
- **Exceptions per location**: Allow negative stock on the locations where you need
  it, such as a production floor or a transit area.
- **Checked on the physical stock**: The quantity on hand in the location, per lot,
  package and owner, not the forecast.
- **Safe for multi-line transfers**: Several lines of the same product in one
  validation are added up, so they cannot overdraw the stock together.
- **Serial numbers, strict or by total**: Per location, check serial-tracked products
  on the serial number of the line or on the total of the location.
- **Point of Sale friendly**: Goods sold at the register have already left the shop, so
  Point of Sale receipts go through by default; each bypass is logged and the shortfall
  stays visible as negative stock to correct.
- **Only products with tracked stock**: Consumables without *Track Inventory* are not
  checked, since Odoo keeps no stock for them.
- **Company setting**: Turn the rule on or off separately for each company.
