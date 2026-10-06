1. Give the **Expected Receipts / Manager** group to the accountants who settle
   card payments (accounting administrators get it automatically) and the
   **Expected Receipts / Card Cashier** group to the people who take card
   payments.
2. Create a bank journal for the account in which the bank transfers the card
   payments (or use the existing one). Its **suspense account** is where card
   payments wait until the bank transfer arrives; on a Romanian company it is
   5125. The account must allow reconciliation. If you want a dedicated
   analytic account (e.g. 5125.01 *Card payments in course of settlement*), set
   it as the suspense account of that journal.
3. Go to **Accounting > Configuration > Card Terminals** and create a terminal
   for each device: the bank journal, the user who uses it by default, the
   matching window (default 4 days) and the alert threshold (default 3 days).
