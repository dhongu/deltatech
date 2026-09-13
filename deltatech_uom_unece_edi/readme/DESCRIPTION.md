Makes UBL and CII electronic invoices use the UN/ECE code configured on the unit
of measure by `deltatech_uom_unece`.

The bridge is needed because `account_edi_ubl_cii` does not call
`uom.uom._get_unece_code()`. It keeps a second copy of the same logic on the
`account.edi.common` abstract model, reading the core dictionary directly.
Without this module a code set on a unit applies to eTransport and is ignored on
invoices — silently, because both documents still validate against their schema.

It lives apart from `deltatech_uom_unece`, and installs itself automatically, so
that the main module stays usable on databases that send no UBL or CII invoice.
