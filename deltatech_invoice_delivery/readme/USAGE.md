1. Create or edit a customer invoice (**Accounting > Customers > Invoices**) and add lines for storable products that are not linked to any existing sale order line.
2. When the invoice is validated (**Confirm**), for each such invoice (that is not a POS order) the module automatically:
   - Creates a sale order for the customer (or reuses the existing one if all unlinked lines belong to a single sale order) with a line for each unlinked storable product, and confirms it.
   - Generates and validates the corresponding delivery from stock, marking the picking as done so stock is moved to reflect the invoiced quantities.
   - Posts a note on the invoice linking to the generated sale order.
3. Sale order lines with a **negative quantity** are allowed (e.g. for corrections/returns) — their stock moves are automatically flagged **To Refund**.
