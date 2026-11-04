Lets you pick the UN/ECE code sent as the unit of measure in electronic documents
(e-invoice, eTransport) on each unit, from the nomenclature ANAF publishes, and
lets several units share the same code.

Since Odoo 20, `account_edi_ubl_cii` has a standard **UN/ECE Code** field on the
unit, filled in for the units shipped by Odoo (square metres, square feet and
millilitres included), and every electronic document reads the code through
`uom.uom._get_unece_code()`. The module is an extension over that field, for what
it does not cover:

- **A nomenclature instead of free text.** The standard field is typed by hand.
  Here the code is picked from the list ANAF publishes with the SAF-T schema, at
  <https://static.anaf.ro/static/10/Anaf/Informatii_R/RO_SAFT_SchemaDefCod_16.02.2026.xlsx>
  (sheet `Unitati_masura`): over two thousand entries from UN/ECE
  Recommendation 20 (units) and 21 (packaging), with the English name and ANAF's
  Romanian translation. Both names load from the same data file, using the
  `name@ro` column syntax Odoo also uses for the Romanian chart of accounts. They
  go into a model of their own rather than a selection field, so a consultant can
  add or correct an entry from the interface when ANAF republishes the list, with
  no code change and no deployment.
- **A code shared by several units.** The standard field is unique: "Box of 13 kg"
  and "Box of 5 kg" cannot both be `XBX` there. The code picked here can be used
  on any number of units.

A code picked here takes precedence over the standard field; when it is empty,
the standard field applies, and then Odoo's built-in mapping (`C62` — one piece —
for any unit it does not recognise). Leaving the field empty keeps exactly the
behaviour you have today, which is what makes the module safe to install on a
running database.
