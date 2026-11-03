1. Go to **Sales → Configuration → Settings**, section **Invoicing** (the setting needs the Sales app, `sale_management`): pick the **Generic Partner** of the
   company and, to keep it from being changed by mistake, tick **Protect Generic Partner**. Save. In a
   multi-company database, repeat this on every company.

   ![Sales settings, Invoicing section: the Generic Partner field set to Generic and the Protect Generic Partner box ticked](static/description/en/01_setari_partener_generic.png)

2. Go to **Invoicing → Configuration → Journals** and tick **Generic Restriction** on the journals that
   must not be used for anonymous customers (usually the banks).

   ![Bank journal form with the Generic Restriction box ticked, above the journal type](static/description/en/02_jurnal_restrictie.png)

3. A customer invoice can be drafted on the generic partner (by hand, from a sale order, a POS or an
   import) and saved as usual.

   ![Draft customer invoice for Generic: two Set pensule pictură at 45 lei on account 707000 with 21% VAT, 108.90 lei in total, and the Confirm button](static/description/en/03_factura_ciorna_generic.png)

4. **Confirm** is refused while the generic partner is the customer or the delivery address of a customer
   invoice or credit note. The message names the field to change: set the real customer and confirm
   again. Vendor bills and journal entries are not affected.

   ![Invalid Operation dialog over the invoice: it cannot be validated because Generic is the generic partner, used for anonymous customers, and it is set as Partner](static/description/en/04_eroare_validare_factura.png)

5. On a new customer payment for the generic partner (**Invoicing → Customers → Payments**), the
   **Journal** list leaves out the restricted journals. The journal proposed when the payment is created
   ignores the restriction, so check it and switch to an allowed one before confirming.

   ![Draft payment for Generic, 108.90 lei: the Journal list is open and proposes only the cash journal Numerar, without the restricted bank](static/description/en/05_plata_jurnale_permise.png)

6. When the protection is on, a user without the **Generic Partner: Editor** group sees a banner on the
   generic partner,

   ![Contact form of Generic opened by a salesperson: a blue banner says it is the generic partner and that changes cannot be saved](static/description/en/06_partener_protejat.png)

   and saving a change, archiving or deleting it is refused. Settings administrators already have the
   **Generic Partner: Editor** group.

   ![Invalid Operation dialog after renaming Generic to Ionescu Andrei: the generic partner is protected and cannot be modified](static/description/en/07_eroare_modificare_partener.png)
