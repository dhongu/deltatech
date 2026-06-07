Streamline your sales workflow by collapsing confirmation, delivery, and invoicing into a
single button click directly on the sale order. Designed for businesses that need to
process straightforward orders quickly — no separate picking validation or invoice wizard
steps required.

**Key features:**

- **Confirm, Deliver and Invoice** — one-click button on draft/sent sale orders that
  confirms the order, validates the delivery (using order quantities), and opens the
  invoice wizard.
- **Deliver and Invoice** — same automated flow available on already-confirmed orders,
  allowing delivery and invoicing in one step.
- **Deliver Notice** — marks the delivery as a notice (`notice = True`) without
  immediately invoicing, then navigates to the resulting picking for review or printing.
- **Invoice button on picking** — adds a direct shortcut to the invoicing wizard from
  the delivery (stock picking) form, so warehouse staff can trigger invoicing from the
  picking view after delivery is done.
- Stock availability is verified before delivery: if any product is not fully available,
  the action is blocked with a clear error message.
- Invoice date is automatically set to today's date.
