1. Install the module on top of `account_edi_ubl_cii`.
2. Issue a customer invoice (`out_invoice`) whose invoice lines are linked to sale order lines that were delivered (the related stock pickings are in the **Done** state).
3. When generating the UBL 2.0 XML export for the invoice (e.g. via e-invoicing/EDI), the picking references are automatically added to the document as a despatch advice (`cac:DespatchDocumentReference`), listing the names of the related pickings.
4. No manual configuration is required; the despatch advice is only added when done pickings are found for the invoice lines.
