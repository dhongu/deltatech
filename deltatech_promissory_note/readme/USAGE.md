1. Open *Invoicing > Accounting > Promissory Notes* (with Odoo Enterprise: *Accounting > Accounting >
   Promissory Notes*). The notes are listed by **Due Date**, with their **Status** and the totals of
   **Amount** and **Cashed Amount**.

   ![The list of promissory notes sorted by Due Date (1), with the Status column (2) showing Cashed, Not Cashed and Cancelled notes, and the totals at the bottom](static/description/en/01_lista_bilete.png)

2. For a note received from a customer, press **New**, fill in **Series and number** and keep
   **Type** = **Customer**: the company becomes the **Beneficiary**. Choose the customer as
   **Issuer**: **Bank Account Issuer** and **Bank Issuer** are taken from the first bank account of
   the customer. Fill in the agreement, due date, amount and currency, check the beneficiary bank
   account and bank, then save.

   ![A customer note in the Not Cashed state: Type Customer (1), Issuer the customer (2), Beneficiary the company (3), Bank Issuer (4) and the Set Cashed button (5)](static/description/en/02_bilet_client.png)

3. For a note issued to a vendor, choose **Type** = **Vendor**: the company becomes the **Issuer**.
   Choose the vendor as **Beneficiary**; its bank account and bank are filled in the same way.

   ![A vendor note: Type Vendor (1), Issuer the company (2) and Beneficiary the vendor (3)](static/description/en/03_bilet_furnizor.png)

4. When the note is cashed, fill in **Cashed Amount** and **Cashed Date** and press **Set Cashed**.
   If **Last note** is ticked, the users of the *Primeste atentionari BO* group receive a message in
   the chatter. **Set Not Cashed** reverts a cashed note; **Cancel** cancels a note that is not cashed.

   ![The last note of an agreement after Set Cashed: Cashed Amount (1), Last note ticked (2), the status bar on Cashed (3) and the notification in the chatter (4)](static/description/en/04_ultimul_bilet_incasat.png)

The module does not create journal entries: the accounting of the notes is done separately. The
two reports in the **Print** menu (*Promissory Note Bill*, *Promissory Note Content*) print an
empty page in this version.
