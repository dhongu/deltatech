Partner GLN
===========

Adds the **GLN (Global Location Number)** on the partner form, on the contact /
address sub-form and on the simplified partner form, as the field `gln`.

Since Odoo 20.0 the GLN is a standard partner identifier (`EAN/GLN`, kept by
`base` in the partner's additional identifiers, and shown by `account` as
`global_location_number` on delivery addresses). This module no longer stores
its own copy: `gln` reads, writes and searches the standard identifier, so the
modules built on `deltatech_gln` (EDI, EDINET, ...) keep working and see the
same value as the standard e-invoicing (UBL/Peppol) code.

The standard validation applies: a malformed GLN (wrong EAN check digit) is
refused.
