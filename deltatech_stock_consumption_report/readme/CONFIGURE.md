- The report reads the transfers to **consumption locations**. With the Romanian localisation
  (`l10n_ro_stock_account`) these are the locations of type *Consumption* and *Usage giving*. Other
  location types can be added by overriding `stock.location._get_consumption_usages()`.
- Access: the report is available to *Inventory / Administrator*; the purposes can be read by every
  inventory user (to pick them on the voucher) and changed by administrators.
