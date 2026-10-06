Card payments taken on a bank terminal reach the bank account days later, as one
grouped transfer per day with no detail. Until then the customer looks unpaid
and the accountant has to split the bank amount by hand. This module registers
the card payment the moment it is received and settles it against the grouped
bank transfer, to the cent.

**Key features:**

- **Card Payment button** on sales orders, on customer invoices and on the
  customer (for an older balance). Partial payments are normal: the remaining
  amount stays due.
- The payment is posted at once on the terminal's bank journal, on the
  journal's suspense account (5125 *Amounts in course of settlement* in
  Romania): the customer's balance drops immediately, the money waits on 5125
  until the bank transfer arrives.
- **Down payment invoice on unbilled orders.** A card payment on an order that
  is not invoiced yet is a down payment: the VAT becomes due when it is
  received. By default the module issues the down payment invoice from the
  order and pays it. A quotation paid by card is confirmed.
- **Expected Receipts register**: every card payment with its terminal, cashier,
  document and state (pending, settled, cancelled), with pivot and graph, a
  search by amount and a *Late* filter for payments not settled after the
  number of days set on the terminal.
- **Card Settlement**: from the bank statement line, the module finds the group
  of pending card payments whose total is exactly the transferred amount
  (exact subset-sum on cents, fast even for 60–80 payments) and reconciles
  them in one click. When two different groups give the same amount, it does
  not choose: it shows both and lets the accountant tick the right one. The
  bank fee is expected on a separate statement line.
- **Cashiers without accounting rights**: the *Card Cashier* group registers
  card payments and sees only its own receipts; the payment is written by the
  module after checking the company, the terminal and the document.
- A scheduled action keeps the register in sync when the accountant reconciles
  from the standard bank reconciliation screen.
- No field is added on sales orders, invoices, payments or companies: the
  settings live on the card terminals.
