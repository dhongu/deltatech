1. In the shop, add a product to the cart and go to checkout. On the **Address** step, fill in
   **Last name** and **First name** (two fields, saved together as "Last name First name"), then
   **Country**, **State / Province**, **Street and Number**, **City**, **Zip Code**, **Email** and
   **Phone**. A private person leaves **Billing details (optional)** unticked.

   ![Checkout address form: Last name and First name in separate fields, then the address, email and phone; below, the optional Billing details section with its checkbox unticked](static/description/en/01_formular_adresa.png)

2. To be invoiced as a company, tick *I am buying as a legal entity (company)* and fill in
   **Company name**, **VAT number (CUI)** (with or without the RO prefix) and the registered office:
   **Registered office county**, **Registered office city**, **Registered office address** and
   **Zip Code**. The registered office is in Romania.

   ![Billing details section ticked, with the company name, its VAT number and the registered office filled in](static/description/en/02_date_facturare_firma.png)

3. Click **Confirm**. A VAT number with a wrong check digit stops the form with *The company VAT
   number (CUI) is not valid.*; missing company data (name, VAT number, registered office city,
   address or zip code) shows *Fill in the company details: name, VAT number (CUI) and registered
   office.* Company billing is available only for deliveries in Romania; otherwise the form shows
   *Billing to a company is available only for deliveries in Romania.* No partner is created until
   the data is corrected.

   ![Address form after Confirm with the VAT number 12345678: the field is red and the message The company VAT number (CUI) is not valid shows above the form](static/description/en/03_cui_invalid.png)

4. With a VAT number that is not recorded yet, the company is created with its registered office
   and becomes the selected **Billing address**; the customer becomes one of its delivery
   addresses and keeps its own address as **Delivery address**.

   ![Delivery step of the checkout: the new company is the selected billing address, with its registered office; the customer is the delivery address](static/description/en/04_checkout_facturare_firma.png)

5. In the backend (**Sales > Orders > Quotations**, or **Orders** once confirmed), the order has the
   customer as **Customer** and **Delivery Address**, and the company as **Invoice Address**. The
   fiscal position and the taxes follow the customer and the delivery address, not the invoice
   address.

   ![Sales order header: Customer and Delivery Address are the customer, Invoice Address is the company](static/description/en/05_comanda_adrese.png)

6. In **Contacts**, the new company has the typed **Tax ID** and registered office, and the
   customer is listed in its **Contacts** tab as a delivery address.

   ![The new company in Contacts: Tax ID and registered office, with the customer as a delivery address in the Contacts tab](static/description/en/06_firma_noua_contacte.png)

7. With the VAT number of a company already recorded (with or without RO), the form asks the same
   fields and does not show the recorded data. The invoice address under that company with the
   name and the registered office typed by the customer is used, or created when none matches
   (the company itself is used when its own data are typed), and is selected as
   **Billing address**. The customer is **not** attached to the company.

   ![Delivery step for a recorded company: the selected billing address is Ana Agro SRL, Ana Agro SRL, with the typed registered office; the delivery address is the customer alone](static/description/en/07_checkout_firma_inregistrata.png)

8. On that order, **Customer** and **Delivery Address** are the customer, and **Invoice Address**
   is the address under the recorded company. Another order with the same name and registered
   office uses the same address; only different data add a new one, which backend users can merge
   from **Contacts** when it differs only in spelling.

   ![Sales order header for a recorded company: Customer and Delivery Address are the customer, Invoice Address is Ana Agro SRL, Ana Agro SRL](static/description/en/08_comanda_firma_inregistrata.png)

The **Billing details** section shows only on the main billing address of a customer who does not
belong to a company and is not a company itself; the others keep the standard company name and VAT fields. The
company is created only from the shop checkout: the address form of the customer portal shows the
section too, but saving it there does not create a company.
