1. In *Accounting > Vendors > Expenses Deduction*, create a report for the employee, with the
   advance amount and date, and click **Advance**: the advance is booked on 542 against the cash
   journal.
2. When the employee returns, add the receipts as lines (amount, tax, supplier, account) and, for a trip, the number of days for the per diem.
   If the employee paid a supplier bill from the advance (for example an older vendor bill), add
   a line of type **Supplier Payment** with that supplier (see below).
3. Click **Validate**: the purchase receipts, their settlement from 542, the per
   diem and the payment of the difference are posted, and the report is **Done**.
4. **Invalidate** reverses a validated report, so it can be corrected.

**Supplier Payment lines.** Validation books the payment as **Dr 401 / Cr 542** and reconciles it
automatically with the supplier's open bills on the same payable account (oldest first), so the
bill is paid or partly paid without any manual matching. If the payment is larger than the open
bills, the rest is an advance to the supplier and is moved to **4092** (Dr 4092 / Cr 401); when the
bill arrives, the accountant offsets it (Dr 401 / Cr 4092). Without a 4092 account in the chart of
accounts, the rest stays as a debit balance on 401. Invalidating the report removes the payment
and the reconciliation: the bill is open again.

Example: an advance of 1,000 RON and receipts of 800 RON leave 200 RON to be returned by the
employee; after validation, the employee's 542 balance is zero.
