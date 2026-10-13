The codes are in **Settings → Technical → UNECE Codes**, filterable by source:
Recommendation 20 for units, Recommendation 21 for packaging (the codes prefixed
with `X`). Both are accepted by UBL/Peppol BIS 3, by CIUS-RO and by the
eTransport schema.

The full nomenclature is loaded on install from the SAF-T schema published by
ANAF, English and Romanian names together, so you should not need to add
anything. When ANAF republishes the list, regenerate the data with
`scripts/import_unece_from_saft.py`.

One caveat on code length: the nomenclature holds `XLTR`, four characters, while
eTransport's own `CodUMType` accepts only two or three. Such a code is reportable
in SAF-T but will be rejected on a transport declaration.

The code itself goes on the unit, in **Settings → Technical → Units of Measure**,
field **UNECE Code**. The field is also available as an optional column in the
list view, which is the quicker way to fill it in for many units at once.

A code set on a unit takes precedence over Odoo's built-in mapping. That is
deliberate: correcting a wrong built-in mapping is half the point of the module.
