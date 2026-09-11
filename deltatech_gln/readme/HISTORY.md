## 19.0.1.1.0

- Hand the `gln` values over to the standard field `global_location_number`
  (module `account_add_gln`, auto-installed with `account`), which now ships the
  same data. Only empty target values are filled, so a correction made on the
  standard side is never overwritten and the migration is safe to re-run;
  partners holding two different values are reported in the log instead.
  This module is on its way out — the copy makes anything reading the standard
  field see the full picture in the meantime.
