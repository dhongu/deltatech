## 20.0.1.1.1

- Own module icon, instead of the generic gears it had.

## 20.0.1.1.0

- Migration to 20.0. The GLN became a standard partner identifier
  (`additional_identifiers["EAN_GLN"]`, module `base`), so `gln` is no longer
  stored: it is a proxy (read / write / search) on the standard identifier and
  gets its validation (EAN check digit). The field is now labelled
  "Global Location Number", so it no longer clashes with the standard `GLN`.
- The migration moves the values of the old `gln` column (and of the 19.0
  `global_location_number` column, if still present) into the standard
  identifiers, without overwriting an existing value. Malformed values and
  conflicting values are reported in the log and left in the old column.

## 19.0.1.1.0

- Hand the `gln` values over to the standard field `global_location_number`
  (module `account_add_gln`, auto-installed with `account`), which now ships the
  same data. Only empty target values are filled, so a correction made on the
  standard side is never overwritten and the migration is safe to re-run;
  partners holding two different values are reported in the log instead.
  This module is on its way out — the copy makes anything reading the standard
  field see the full picture in the meantime.
