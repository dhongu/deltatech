## 19.0.1.2.0 (2026-11-26)

- **Deprecated.** `gln` is now a bridge: a related field (`readonly=False`) on the standard
  `global_location_number` of `account_add_gln`, without its own column, so code and data that
  still read or write `gln` keep working. The module depends on `account_add_gln`.
- The migration copies `gln` into the standard field where that one is empty; when both are set
  and differ, the standard value is kept and each partner is logged. The old `gln` column is left
  in the database, untouched, as a backup.
- The partner form shows the standard GLN on every partner, not only on delivery addresses; the
  duplicate *GLN* field (and the "same label" warning at every load) is gone.
- The EDI modules (`deltatech_edi` and its connectors) no longer depend on this module. It is not
  migrated to 20.0, where the GLN is part of `account`.
- No consultant sheet (`consultant_sheet: none`): a deprecated technical bridge, without a screen or a
  flow of its own; the GLN a consultant sets up is the standard field, described in the sheet of
  `deltatech_edi`.

## 19.0.1.1.1

- Own module icon, instead of the generic gears it had.

## 19.0.1.1.0

- Hand the `gln` values over to the standard field `global_location_number`
  (module `account_add_gln`, auto-installed with `account`), which now ships the
  same data. Only empty target values are filled, so a correction made on the
  standard side is never overwritten and the migration is safe to re-run;
  partners holding two different values are reported in the log instead.
  This module is on its way out — the copy makes anything reading the standard
  field see the full picture in the meantime.
