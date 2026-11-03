# History

## 19.0.1.0.1

- Consultant sheet and screenshots: goods used internally go first to a materials location
  (Dr 3028 = Cr 371 at cost) and are then issued for consumption; goods issued straight from the
  sale stock (Dr 607 = Cr 371) are shown as an anomaly found with the *Delivered to customers*
  column. The *Consumption account* on 607 is no longer recommended.

## 19.0.1.0.0

- First version: consumption purpose on the consumption voucher, report by store and purpose
  (pivot and XLSX, summary and detail).
- The value of a consumption is taken from the journal entry of the voucher (the credit of the
  product lines, i.e. the stock leaving the stock account); the stock value of the move is used
  only when there is no entry.
- Consumption purposes are per company (multi-company record rule; purposes without a company are
  shared).
