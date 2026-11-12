Checkout address form for Romanian shops, with optional company billing.

- The address is asked in the Romanian order: last name, first name, country, county, street,
  city, zip code, then email and phone. The last name and the first name are kept together in the
  name of the contact.
- Below the address, an optional **Billing details** section: a customer who buys as a
  company ticks *I am buying as a legal entity (company)* and types the company name, its
  VAT number (CUI) and its registered office (county, city, street, zip code). The CUI is
  checked (checksum) before the order goes further.
- When no company is recorded with this CUI, the company is created as a company partner,
  with its registered office, and the customer becomes one of its delivery addresses, keeping
  its own address. The order is invoiced to the company and delivered to the customer.
- When a company is already recorded with this CUI (with or without the RO prefix), a new
  invoice address is created under it with the name and the registered office typed by the
  customer, and the order is invoiced to it; the checkout shows it as the selected billing
  address. Of the recorded company only its name shows (as the parent of the address, a
  public data of the CUI); its recorded address and contacts do not, and the customer is
  **not** attached to it: typing a CUI must not give a visitor the documents of another
  company. The form asks the same fields whether or not the CUI is known. The invoice
  addresses typed this way can be reviewed or merged by the backend users.
- The company billing is available only for deliveries in Romania: the fiscal position of the
  order follows the customer and the delivery address, not the invoice address, and the
  domestic VAT of a Romanian company applies to goods delivered in Romania.
- The CUI is saved as typed, without spaces, dots and hyphens (with or without the RO prefix); whether the company is registered
  for VAT is not checked with ANAF, so the accountant reviews the new companies before
  invoicing.
- Customers who already belong to a company, or are one, keep the standard company name and VAT
  fields.
