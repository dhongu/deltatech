1. Create a purchase order in EUR for a supplier who bills in RON (**Purchase → Orders →
   Purchase Orders**). On the **Other Information** tab, set **Invoicing Journal** to the vendor bills
   journal without currency, then confirm the order.

   ![Purchase order in EUR with the Invoicing Journal set on the Other Information tab](static/description/en/01_comanda_jurnal_facturare.png)

2. In the purchase order list, select the order and click **Create Bills** (or use **Upload
   Bill** on the order form with the supplier PDF).

   ![Purchase order list with the order selected and the Create Bills button](static/description/en/02_creare_factura_din_lista.png)

3. The bill is in RON, on the order journal, with the EUR prices converted at today's rate
   (the last rate dated on or before the day).

   ![Draft bill in RON on the order journal, with the converted price](static/description/en/03_factura_lei_curs_azi.png)

4. Set the **Bill Date** from the supplier invoice: the prices are converted again from the order
   price, at the rate of that date. Changing the bill **Currency** converts them again too, and
   price changes made by hand on order lines are lost, so correct prices after the date is final.

   ![Draft bill with the Bill Date set and the price converted at that date's rate](static/description/en/04_factura_data_reconversie.png)

Leave **Invoicing Journal** empty for suppliers who bill in the order currency: the bill stays in
EUR with the order price, as in standard Odoo.

![Bill in EUR for an order without invoicing journal](static/description/en/05_factura_fara_jurnal_eur.png)

With a journal in EUR on the order, the bill is created in that journal, in EUR, with the order
price.

![Bill in EUR on the journal chosen on the order](static/description/en/06_factura_jurnal_eur.png)

If the bill line is in another unit of measure than the order line (e.g. Dozens instead of
Units), the order price is first brought to that unit, then converted. Change the Unit before
setting the Bill Date, or set the date again after changing it.

![Bill line in Dozens with the price brought to the dozen and converted](static/description/en/07_factura_unitate_duzina.png)

A new vendor bill completed from the order with **Auto-Complete** takes the order invoicing
journal and currency, with the converted prices.

![New vendor bill auto-completed from the order, in RON on the order journal](static/description/en/08_factura_completare_automata.png)

When several orders of the same vendor are billed together from the list, Odoo groups them by
vendor and bill currency, not by journal: orders with different journals but the same bill
currency end up on one bill, in the journal of the first order. Bill them one by one to keep the
journals apart.

**Vendor Rate**, in the bill header under the dates, shows the Odoo (BNR) rate of the bill date
(bill currency for 1 unit of the order currency, e.g. 5.0912 RON for 1 EUR). If the supplier
invoice states another rate, type it there **after setting the Bill Date**: the order prices are
converted at that rate. Changing the Bill Date afterwards brings the Odoo rate of the new date
back and a warning names the rate it replaced; clearing the field also puts the Odoo rate back.
The field is shown only when the bill lines come from orders in one other currency.

![Draft bill in RON with Vendor Rate 5.100000 RON per 1 EUR and the Bill Date set: the price is 12.50 EUR × 5.10 = 63.75](static/description/en/09_factura_curs_furnizor.png)

![Vendor rate replaced dialog after the Bill Date was changed: the vendor rate 5.1000 was replaced with the rate of the new date, 5.0912 RON for 1 EUR, and the price is converted again to 63.64](static/description/en/10_avertisment_curs_inlocuit.png)
