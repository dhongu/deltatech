**Configure**

1. In **Sales → Configuration → Settings** (Sales app, `sale_management`), **Sales** tab, **Invoicing** section, choose the
   **Generic Partner** (the *Generic* contact created by the module, or any other) and, optionally, tick
   **Protect Generic Partner**.

   ![Sales settings, Invoicing section: Generic Partner and Protect Generic Partner](static/description/en/01_setari_partener_generic.png)

2. On the bank and cash journals that must not be used for the generic partner, tick **Generic
   Restriction** (**Invoicing → Configuration → Accounting → Journals**).

   ![Bank journal with Generic Restriction ticked](static/description/en/02_jurnal_restrictie_generic.png)

**Protected generic partner**

1. A user without the **Generic Partner: Editor** group sees a warning banner on the generic partner.
   Settings administrators have the group.

   ![Generic partner form with the protection banner](static/description/en/03_partener_generic_protejat.png)

2. Saving a change, archiving or deleting the partner is refused.

   ![Error dialog: the generic partner is protected and cannot be modified](static/description/en/04_modificare_refuzata.png)

**Invoices and payments**

1. A customer invoice or credit note whose customer or delivery address is the generic partner cannot be
   confirmed: set the real customer first. Drafts stay allowed.

   ![Draft invoice for the generic partner with the error asking for the real customer](static/description/en/05_factura_validare_refuzata.png)

2. A payment for the generic partner, new or registered from an invoice, proposes only the bank and cash
   journals without **Generic Restriction**.

   ![Draft payment for the generic partner: the Journal list shows only the allowed journals](static/description/en/06_plata_jurnale_permise.png)
