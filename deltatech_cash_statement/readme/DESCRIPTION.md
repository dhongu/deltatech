This module keeps the balances of cash statements consistent with the
accounting, and books a counted cash difference as a dated entry instead of
silently overwriting a balance.

**Key features:**

- A wizard on the bank statement list (**Action → Cash Update Balances**) with
  two modes:
  - **Align with the accounting balance**: the starting balance of the first
    selected statement becomes the balance of the cash account from the posted
    entries dated before it, and each following statement starts from the real
    ending balance of the previous one. No journal entry is created.
  - **Register a cash difference**: when the counted cash differs from the
    accounting balance, a statement line dated on the inventory date books the
    difference on the income account (surplus) or the expense account
    (shortage). On a Romanian company the defaults are 7588 and 6588; elsewhere
    the cash difference accounts of the journal. The account can be changed,
    e.g. to 4282 when the shortage is charged to the cashier.
- The difference is never hidden: a statement balance that does not match the
  cash account can only be corrected through a dated, documented entry.
