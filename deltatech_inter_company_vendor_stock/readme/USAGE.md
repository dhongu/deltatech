Two companies of the same group work in one Odoo database: the vendor company keeps the stock, the
selling company buys from it and sells to its own customers. On the product, the selling company has
a vendor line whose vendor is the partner of the vendor company.

1. **Check the vendor line (selling company).** Open the product, then its vendor line with the
   vendor company. The **Quantity Available** field shows the free stock of the vendor company, as
   written by the module at the last reservation or validation.

   ![Vendor line in the selling company: vendor Furnizor Grup SRL, vendor product code PS-1CP, Quantity Available 12.00, company Distribuitor Grup SRL](static/description/en/01_linie_furnizor.png)

2. **Reserve a delivery (vendor company).** When the vendor company reserves stock on a delivery,
   the module recomputes the free stock of the product and writes it on the vendor line. The
   delivery is **Ready**.

   ![Delivery of the vendor company in the Ready state, with 3 units reserved](static/description/en/02_rezervare.png)

3. **Validate the delivery (vendor company).** On **Validate**, the module updates the vendor line
   again, with the free stock left after the delivery. The delivery is **Done**.

   ![Delivery of the vendor company in the Done state, with 5 units delivered](static/description/en/03_validare.png)

4. **See the vendor stock on a quotation (selling company).** On the order lines, the optional
   **Vendor Quantity Available** column (from Vendor Stock) shows the same free stock of the vendor.

   ![Quotation of the selling company: the product line with 2 units and Vendor Quantity Available 12.00](static/description/en/04_comanda_vanzare.png)

A vendor line set on a product variant gets the free stock of that variant; a line without a variant
(the usual case when you add it from the product form) gets the free stock of all the variants of
the product.
