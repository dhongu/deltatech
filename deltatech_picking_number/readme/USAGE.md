1. Go to **Inventory > Configuration > Operations Types**, open an operation type
   (e.g. Receipts, Deliveries) and set a **Sequence on Request** — a second
   `ir.sequence`, separate from the regular picking naming sequence.
2. On a transfer (`stock.picking`) of that operation type, a new **Allocate number**
   button appears next to the confirm button (before the transfer has a request
   number assigned).
3. Click **Allocate number** to draw the next value from the second sequence; it is
   stored in the new **Request Number** field and also used to set the transfer's
   **Reference**.
4. Once a transfer has been numbered this way, it can no longer be deleted (an error
   is raised if you try), to keep the allocated number from being reused.
