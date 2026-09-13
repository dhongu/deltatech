Lets you set the UN/ECE code sent as the unit of measure in electronic documents
(e-invoice, eTransport) on each unit, instead of relying on the fixed mapping
built into Odoo.

Odoo matches a unit to its code exclusively through the XML ID, against a
dictionary of 28 entries, and returns `C62` — one piece — for anything it does
not recognise, without raising an error. That has two consequences, both silent:

- **Every unit you create is declared as a piece.** A reception of 10 boxes of
  13 kg leaves for the tax authority as `C62`, whatever it actually measures.
  There is no data fix: a unit like "Box of 13 kg" has no entry in the built-in
  dictionary to point at.
- **Some units shipped by Odoo are declared as pieces too.** The dictionary
  looks for `uom.uom_square_meter` and `uom.uom_square_foot`, while the data
  defines `uom.product_uom_square_meter` and `uom.product_uom_square_foot`; the
  millilitre is missing altogether. Square metres, square feet and millilitres
  all travel as `C62`. This module corrects the three of them on install.

The codes come from the nomenclature ANAF publishes with the SAF-T schema, at
<https://static.anaf.ro/static/10/Anaf/Informatii_R/RO_SAFT_SchemaDefCod_16.02.2026.xlsx>
(sheet `Unitati_masura`): over two thousand entries from UN/ECE Recommendation 20
(units) and 21 (packaging), with the English name and ANAF's Romanian
translation. They are loaded into a model of their own rather than a selection
field, so a consultant can add or correct an entry from the interface when ANAF
republishes the list, with no code change and no deployment.

Both paths that build electronic documents are covered: eTransport reads the
code through `uom.uom._get_unece_code()`, while UBL and CII invoices reach it
through a separate method of their own, on `account.edi.common`. Overriding only
the first would have fixed eTransport and silently left invoices unchanged.

Leaving the field empty keeps exactly the behaviour you have today, which is
what makes the module safe to install on a running database.
