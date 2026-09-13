Nothing to do day to day: once a unit carries a code, every electronic document
built from it uses that code.

To check what will be sent, open the unit and read the **UNECE Code** field. An
empty field means Odoo's built-in mapping applies — `C62` for any unit the
standard does not recognise.

If invoices go out as UBL or CII, install `deltatech_uom_unece_edi` as well. It
installs itself automatically when `account_edi_ubl_cii` is present, and without
it the code applies to eTransport but is ignored on invoices.
