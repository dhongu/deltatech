Nothing to do day to day: once a unit carries a code, every electronic document
built from it uses that code.

To check what will be sent, open the unit and read the **UNECE Code** field. An
empty field means Odoo's built-in mapping applies — `C62` for any unit the
standard does not recognise.

The code applies to both paths that build electronic documents: eTransport,
through `uom.uom._get_unece_code()`, and UBL/CII invoices, which reach the same
value through a separate method of their own.
