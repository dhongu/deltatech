Monthly report of the consumption vouchers (transfers to consumption locations), for the
accountant. Opened from *Inventory → Reporting → Consumption report*: pick the period and,
optionally, the operation types (one per store or warehouse), then *View* (pivot) or *Export XLSX*.

Features:

- **Consumption purpose** on the consumption voucher (investments, own use...), chosen from the
  list in *Inventory → Configuration → Consumption purposes*; required on new vouchers and copied
  on returns.
- **Consumption locations**: with the Romanian localisation (`l10n_ro_stock_account`), the
  locations of type *Consumption* and *Usage giving*; other modules can extend the list
  (`stock.location._get_consumption_usages()`).
- **Value from accounting**: the value of a consumption is the credit of the product lines in the
  journal entry of the voucher (the stock leaving the stock account); without an entry, the stock
  value of the move.
- **XLSX export** with two sheets: a summary by store and purpose (products, quantity, value) and a
  detail by store, purpose and product, with category, average cost, *can be sold* flag and the
  quantity delivered to customers in the last 6 months, so goods meant for sale are easy to spot.
