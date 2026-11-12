Orders received in full and billed at once should not need three separate steps. This module adds purchase order buttons that confirm, receive and bill in one click.

- **One-click flow**: After a prompt, the *Confirm, Receipt and Bill* button on a draft order, or *Receipt and Bill* on a confirmed one, confirms the order if needed, receives it and creates and opens the vendor bill.
- **Automatic receipt**: Each ready receipt is validated with the ordered quantities and the order date as period date. Its source document becomes the order's vendor reference, or the order name, and its notice mark is cleared. A waiting receipt is reserved first; if that fails, the action stops with *The stock transfer cannot be validated!*
- **Receipt Notice**: The *Receipt Notice* button on a confirmed order sets the notice mark on its ready receipts and opens the order's receipts, without validating anything.
- **Invoice from receipt**: A done receipt of a purchase order shows an *Invoice* button, which opens the vendor bills of the order and passes the notice mark on.

The module depends on `purchase_stock` and `stock`; the order buttons are for internal users. The *Confirm, Receipt and Bill* button also appears on a sent quotation, which it does not confirm or receive. The notice mark is only stored and passed on.
