This module works automatically, with no configuration needed.

- On a confirmed Purchase Order, when the quantity to invoice is negative for
  any line (e.g. after a return, the received/delivered quantity is now lower
  than what was already invoiced), clicking **Create Bill** from the order
  automatically opens a **Credit Note** (`in_refund`) instead of a regular
  vendor bill, pre-filled with the returned quantities.
- On a draft vendor credit note, a **Purchase Order** field is available so it
  can be linked back to the originating order if it was not created directly
  from that order.
