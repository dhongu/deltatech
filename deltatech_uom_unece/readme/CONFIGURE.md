The codes are in **Settings → Technical → UNECE Codes**. The module ships the
subset in current use — mass, volume, length, area, count, packaging, time and
energy. Add what you are missing from the UN/ECE Recommendation 20 (units) and
Recommendation 21 (packaging, the codes prefixed with `X`) lists; both are
accepted by UBL/Peppol BIS 3, by CIUS-RO and by the eTransport schema.

The code itself goes on the unit, in **Settings → Technical → Units of Measure**,
field **UNECE Code**. The field is also available as an optional column in the
list view, which is the quicker way to fill it in for many units at once.

A code set on a unit takes precedence over Odoo's built-in mapping. That is
deliberate: correcting a wrong built-in mapping is half the point of the module.
