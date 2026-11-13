Sales orders and invoices should be issued to the company, with the invoice and delivery addresses taken from its contacts. This module keeps the selection lists on those documents to the right partners and lets you mark which address of a customer is proposed by default.

- **Company as customer**: The customer field of sales orders and invoices lists only partners without a parent company, so a contact person cannot be picked in place of the company.
- **Matching addresses**: On a sales order, the invoice address lists only the *Invoice* addresses of the chosen customer, and the delivery address only its *Delivery* addresses.
- **Default address**: A *Contact Default* checkbox on the invoice and delivery addresses marks the one that Odoo proposes on new documents. Ticking it clears the mark on the other addresses of the same type of that customer.
- **Green Invoice**: A *Green Invoice* checkbox on the customer form is for customers who prefer paperless invoices. When their invoice is sent, the PDF is no longer downloaded by default and the invoice is e-mailed instead; the PDF can still be downloaded by ticking it in the sending window.

The module depends on Sales, Contacts, Invoicing and *Contact Personal Data* (`deltatech_contact`). The restrictions are filters on the selection lists of the forms: records created by import or through the API are not checked.
