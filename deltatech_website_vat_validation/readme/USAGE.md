The module has no settings of its own. Its checks run when a **logged-in** customer saves an
address form: the **Address** step of the website checkout, and **My Account → Edit information**
(the **Details** page) or **Addresses** in the customer portal. A visitor checking out without an
account is not checked, so the form cannot be used to find out who is a customer.

**1. A tax code of another company, at checkout**

In the cart, the customer clicks **Checkout** and reaches the **Address** step, where their
addresses are shown as cards. The pencil on the billing address card opens **Edit address**.
In **VAT** they type
the tax code of a company that already has an account, here ` ro 12 34 567 ` (lower case, spaces
around and inside), and click **Confirm**. The spaces are removed and the code is compared without
its country prefix, so it matches `RO1234567` of an existing customer. The **VAT** field is marked
in red and the message above the form asks the customer to get access from a colleague or to
contact the shop. The company found is not named. With `deltatech_b2b_portal`, the message points
to the access request form of the `/b2b` page instead.

![Address step of the checkout: the VAT field with ro 12 34 567 marked in red and, above the form, the message that a company with this tax code already has an account, asking to get access from a colleague or to contact the shop](static/description/en/01_cod_fiscal_duplicat_checkout.png)

**2. An e-mail address of another account, at checkout**

On the same step, an **Email** that belongs to another customer is refused: the field is marked in
red and the message asks the customer to log in with that account or to use another address.

![Address step of the checkout: the Email field with an address of another customer marked in red and the message that this e-mail address belongs to another account](static/description/en/02_email_duplicat_checkout.png)

**3. The same check in the customer portal**

In **My Account → Edit information**, the same tax code is refused with the same message when the
customer clicks **Save Address**; nothing is saved.

![Details page of the customer portal: the VAT field with ro 12 34 567 marked in red and the message that a company with this tax code already has an account](static/description/en/03_cod_fiscal_duplicat_portal.png)

What is not a duplicate: the tax code and e-mail of the customer's own company and of its contacts,
and any phone number, since colleagues share the company phone and relatives a home phone.

**4. Display Product Prices keeps its value**

In **Website → Configuration → Settings**, section **eCommerce**, choose **Display Product Prices**:
**Tax Excluded** or **Tax Included**. Odoo recomputes this setting whenever the fiscal country of the
website company is recomputed, for example after the address of the company's own partner is
rewritten by a partner sync, and without the module it falls back to **Tax Excluded**. With the
module, the saved value stays.

![Website settings: Display Product Prices highlighted, with Tax Included selected](static/description/en/04_afisare_preturi_pastrata.png)

**5. The buying company is created from the billing address**

At checkout, in the billing address, a customer who buys for a company fills in the standard
**Company Name** and **VAT** fields. When the address is saved, the company is created as a partner
(a **Company**, with the address and the tax code typed) and the customer becomes its contact, so
the order and its invoice go to the company. This happens only when the address is used for billing,
the customer is not already a company or the contact of one, both fields are filled in and no other
customer has this tax code. A visitor (not logged in) who types the tax code of a customer keeps it on
their own address and is not attached to that company.

![Contacts: the partner Beta Construct SRL, a Company, with its VAT number highlighted and, in the Contacts tab, the customer Mihai Pop highlighted](static/description/en/05_firma_creata_la_comanda.png)
