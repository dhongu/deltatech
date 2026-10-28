1. In *Accounting > Vendors > Expenses Deduction*, create a report for the employee, with the
   advance amount and date, and click **Advance**: the advance is booked on 542 against the cash
   journal.
2. When the employee returns, add the receipts as lines (amount with VAT included, supplier,
   account) and, for a trip, the number of days for the per diem.
3. The accountant clicks **Validate**: the purchase receipts, their settlement from 542, the per
   diem and the payment of the difference are posted, and the report is **Done**.
4. **Invalidate** reverses a validated report, so it can be corrected.

**Supplier payment.** A line of type *Supplier Payment* is a bill paid by the employee from the
advance (Dr 401 = Cr 542). Its **Bills Paid** button lists the supplier bills it pays, with the
amount allocated to each (partial payments allowed); without bills, it settles the oldest open
bills first. The unallocated part stays on 401 as an unallocated payment of the supplier.

**Settlement mode.** *Cash* pays the advance from the cash register. *Bank transfer (personal
card)* pays it from a bank journal: Dr 542 = Cr 5125 (outstanding payments), matched with the bank
statement line (Dr 5125 = Cr 5121); a refund is Dr 5125 = Cr 542. *Company card* has no advance: the
receipts were paid by the company, so each one is settled Dr 401 = Cr 5125 of the card journal and
matched with the card statement; only the per diem is owed to the employee and paid from the payment
journal. A cash withdrawal with the company card is a separate *Bank transfer* report (Dr 542 =
Cr 5121).

**Foreign currency.** A report on a foreign currency cash journal is kept in that currency: the
advance, the receipts, the per diem and the difference are entered in the currency, and each
journal entry carries the currency amount and its company currency value at the exchange rate of
its date (the advance at the advance date, each receipt at its date, the per diem and the
difference at the expense date). At validation, 542 is closed in the currency and the remaining
company currency balance is posted as exchange difference: Dr 665 = Cr 542 (loss) or Dr 542 =
Cr 765 (gain).

Example: an advance of 1,000 RON and receipts of 800 RON leave 200 RON to be returned by the
employee; after validation, the employee's 542 balance is zero.
