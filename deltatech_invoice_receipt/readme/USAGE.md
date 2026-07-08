This module works automatically in the background when you post vendor bills; there is no dedicated menu, button, or settings screen to configure.

1. Create a vendor bill (Accounting > Vendors > Bills) and enter the invoice lines and the **Bill Date**, then click **Confirm**.
2. Before posting, the module checks whether each stockable product line is already linked to a purchase order line:
   - If a matching confirmed purchase order is found, it links the bill lines to it.
   - If no purchase order exists for one or more lines, a new purchase order is created automatically for the vendor (referencing the bill), grouping all unmatched lines together.
3. If the generated/linked purchase order is not yet confirmed, posting is blocked and a notification asks you to confirm the purchase order first.
4. Once the purchase order is confirmed, the module automatically validates the corresponding receipt (stock picking), setting the received quantities to match the ordered quantities, so you do not need to manually process the incoming shipment.
5. Purchase order lines with a negative quantity are allowed (e.g. for returns/credit scenarios) and are turned into a return picking automatically when the order is processed.
