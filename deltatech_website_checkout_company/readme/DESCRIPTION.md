Checkout address form for Romanian shops, with optional company billing.

- The address is asked in the Romanian order: last name, first name, country, county, city,
  street, then email and phone. The last name and the first name are kept together in the
  name of the contact.
- Below the address, an optional **Billing details** section: a customer who buys as a
  company ticks *I am buying as a legal entity (company)* and types the company name, its
  VAT number (CUI) and the county and city of its registered office. The CUI is checked
  (checksum) before the order goes further.
- When no company is recorded with this CUI, the company is created as a company partner,
  with its registered office, and the customer becomes one of its delivery addresses, keeping
  its own address. The order is
  invoiced to the company and delivered to the customer.
- When a company is already recorded with this CUI (with or without the RO prefix), the order
  is invoiced to it and the customer is **not** attached to it: typing a CUI on the website
  must not give a visitor access to the documents of the company in the portal. Attaching the
  contact to the company is left to the backend users. The checkout and payment pages show
  the company as the billing address (name, registered office, CUI): these are the public
  details of the company in the trade register and at ANAF, found by anyone from the CUI;
  the contacts, the documents and the other data of the company are not shown.
- Customers who already belong to a company keep the standard company name and VAT fields.
