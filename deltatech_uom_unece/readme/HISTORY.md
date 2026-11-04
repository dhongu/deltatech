## 20.0.1.0.1 (2026-11-04)
- Migration to 20.0. Odoo now has a standard UN/ECE Code field on the unit and
  reads the code through `uom.uom._get_unece_code()` for every electronic
  document: the override on `account.edi.common` is gone, and so is the data that
  fixed square metres, square feet and millilitres, which the standard now covers.
  The code picked from the nomenclature still wins over the standard field.

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
