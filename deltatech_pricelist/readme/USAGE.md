1. Open the company (*Settings > Users & Companies > Companies*). Under **Currency** (the accounting
   currency), choose the **Price List Currency**: the currency in which the sales prices of all the
   products of the company are kept. Save.

   ![Company form, General Information tab: Currency (1) is RON and Price List Currency (2) is EUR](static/description/en/01_moneda_lista_preturi_companie.png)

2. Check that the price list currency has a rate (*Invoicing > Configuration > Accounting > Currencies*,
   open **EUR**, tab **Rates**). Odoo uses the last rate up to the date of the document.

   ![The EUR currency, Rates tab: one rate (1) for Nov 4, Unit per RON 0.200000000000 and RON per Unit 5.000000000000](static/description/en/02_curs_eur.png)

3. Open the product (*Sales > Products > Products*) and enter the **Sales Price** in the price list
   currency: the currency symbol (€) is shown next to it. The **Cost** stays in the company currency.

   ![Product form: Sales Price (1) is 120.00 € and Cost (2) is 400.00 lei](static/description/en/03_pret_vanzare_eur_produs.png)

4. Create a quotation (*Sales > Orders > Quotations*) with a pricelist in the company currency, or with
   no pricelist, and add the product: the **Unit Price** is the sales price converted at the rate of the
   quotation/order date, here 120.00 € × 5 = 600.00 lei.

   ![Quotation with the pricelist RON prices (RON) (1): the Unit Price (2) of the pump is 600.00, the amount for 2 units 1,200.00 lei](static/description/en/04_comanda_vanzare_pret_ron.png)

A pricelist in the same currency as the sales price (EUR) does not convert it. On a pricelist in another
currency, **Discount** and **Formula** rules start from the converted price; **Fixed Price** amounts are
already in the pricelist currency. A quotation keeps the price computed when the line was added, at the
rate of its quotation/order date: it does not follow a later rate by itself. Customer invoices created without a sales order
convert the sales price in the same way.
