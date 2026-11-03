Asks customers to rate the products they bought, by e-mail, a few days after the invoice.

**Feedback e-mail per invoice.** The *Invoice: request feedback* e-mail template lists the lines of a
customer invoice, each with the product image, a link to the product page, the quantity and three
rating links (*Satisfied*, *Not satisfied*, *Highly Dissatisfied*). Section and note lines are shown as
headings. The e-mail is posted in the chatter of the invoice and sent right away.

**Rating on the product.** Each product line gets its own rating record on the product template, so
a click on a rating link records the customer's rating for that product through the standard
`/rate` page of Odoo.

**Scheduled sending.** The *Request Feedback* scheduled action (inactive at install) runs once a day
and sends the e-mail for the posted customer invoices dated a given number of days ago, 3 by default,
of the companies where *Email feedback after sale* is enabled. The delay is read from the
`sale.days_request_feedback` system parameter (*Settings > Technical > Parameters > System
Parameters*).

**Manual sending.** On customer invoices, *Actions > Request feedback* sends the e-mail for the
selected invoices, whether the option is enabled or not.

**Template per company.** In *Sales > Configuration > Settings*, the *Email feedback after sale*
option shows the *Email Template Request Feedback* field, where another e-mail template on invoices
can be chosen for the company. Without one, the module's own template is used.

**Links on the company website.** When the invoice company has a website address, the links in the
e-mail are built on that address instead of the database `web.base.url`.

## Limitations

- The delay in days has no field in the settings; it is changed only through the system parameter.
