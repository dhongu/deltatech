**Note:** this module is marked *Obsolete* — the GLN support has been superseded and it should not be installed on new databases.

1. Requires `deltatech_gln` (which adds the GLN field on the partner) and `account_edi_ubl_cii`.
2. Set the **GLN** code on a partner record.
3. When exporting a UBL 2.0 invoice for that partner, the GLN is automatically included as a party identification node (scheme ID `0088`) in the generated XML.
