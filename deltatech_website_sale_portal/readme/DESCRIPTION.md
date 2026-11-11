Customers who order often keep their own reference on every order, but the customer portal lists their quotations and orders only by Odoo's order number. This module adds a reference column and a search box to those two lists, so a customer can find a document by the number they know.

- **Reference column**: The *Customer Reference* of the sales order is shown right after the order number, in both the *Quotations* and the *Orders* lists.
- **Search box**: A search box above the lists lets the customer choose where to search: in the order name, in the customer reference, or in both (the default).
- **Partial matches**: The search matches part of the text and ignores upper and lower case, so a few digits of a reference are enough.
- **Extra sorting**: The lists can also be sorted by order name or by customer reference.
- **Search kept across pages**: The search stays active when the customer moves to the next page of results, and the searched text remains visible in the box.

The module extends the customer portal of the Sales app and depends on *eCommerce* (`website_sale`). It changes only the quotation and order lists; invoices and the other portal documents stay as they are.
