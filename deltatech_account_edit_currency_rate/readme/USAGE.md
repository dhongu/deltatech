1. **Create a foreign-currency invoice.** Go to **Invoicing (or Accounting) → Customers →
   Invoices** and click **New**. Choose the customer, set the **Currency** to EUR and add the invoice lines. The invoice
   is converted at the official rate of the invoice date, shown under the currency.

   ![Draft customer invoice in EUR: one line of 100.00 EUR with 21% VAT on account 704000, total 121.00 EUR; under the Currency field, the official rate 1 RON = 0.201207 EUR](static/description/en/01_factura_ciorna.png)

2. **Enter the custom rate.** Open the **Other Info** tab. In the **Accounting** group, under
   **Fiscal Position**, fill in **Currency Rate Custom** as company currency per one unit of the
   invoice currency (for example `5.0000` RON per EUR). The field is shown only when the invoice
   currency differs from the company currency. The company-currency amounts, the taxes and the
   totals are recomputed at once; the same happens when the invoice is created or updated through
   import or an integration. The custom rate applies to invoices only: it is not shown on journal
   entries, and a custom rate sent to a journal entry through import or an integration is refused.

   ![Other Info tab of the draft invoice: in the Accounting group, under Fiscal Position, the highlighted Currency Rate Custom field set to 5.0000; under Currency the rate becomes 1 RON = 0.200000 EUR](static/description/en/02_curs_propriu.png)

3. **Check the company-currency amounts.** In the **Journal Items** tab, check the **Debit** and
   **Credit** columns: for 100 EUR at 5.0000 the income is 500.00, the VAT 105.00 and the customer
   605.00 in company currency. Then click **Confirm**.

   ![Journal Items tab at the rate 5.0000: 704000 services income credit 500.00, 442700 VAT credit 105.00 and 411100 customers debit 605.00](static/description/en/03_elemente_jurnal.png)

4. **Posted invoice.** Once the invoice is confirmed, the custom rate can no longer be changed. To
   change it, click **Reset to Draft**, correct the rate and confirm again.

   ![Posted invoice INV/2026/00001 with the Other Info tab open: the highlighted Currency Rate Custom field shows 5.0000 and is read-only](static/description/en/04_factura_confirmata.png)

5. **Duplicate and credit note.** A duplicated invoice does not copy the custom rate and starts
   from the official rate. A credit note created with **Credit Note** keeps the rate of the
   original invoice, so it reverses the same company-currency amounts.

   ![Posted credit note RINV/2026/00001, reversal of INV/2026/00002, with the Other Info tab open: the highlighted Currency Rate Custom field keeps 5.0000, the rate of the original invoice](static/description/en/05_nota_credit.png)
