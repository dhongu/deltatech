Asks customers to rate the products they bought, by e-mail, a few days after the invoice.

**Feedback e-mail per invoice.** The *Invoice: request feedback* e-mail template lists the lines of a
customer invoice, each with the product image, a link to the product page, the quantity and three
rating links (*Satisfied*, *Not satisfied*, *Highly Dissatisfied*). Section and note lines are shown as
headings.

**Rating on the product.** Each product line gets its own rating record on the product template, so
a click on a rating link records the customer's rating for that product through the standard
`/rate` page of Odoo.

**Scheduled sending.** The *Request Feedback* scheduled action (inactive at install) runs once a day
and sends the e-mail for the customer invoices dated a given number of days ago, 3 by default. The
delay is read from the `sale.days_request_feedback` system parameter
(*Settings > Technical > Parameters > System Parameters*).

**Manual sending.** On customer invoices, *Actions > Request feedback* sends the e-mail for the
selected invoices.

**Links on the company website.** When the invoice company has a website address, the module tries
to build the links in the e-mail on that address instead of the database `web.base.url`.

## Limitations

- On 19.0 the sending does not work: the code still calls `xmlid_to_res_id` and
  `message_post_with_template`, which no longer exist in Odoo, so both the scheduled action and
  *Request feedback* stop with an error. The subject, sender, recipient and language of the template
  also use the old `${...}` syntax, which is no longer rendered.
- The *Email feedback after sale* option and its e-mail template in *Sales > Configuration >
  Settings* are stored but not used: the e-mail always uses the module's own template, whatever the
  option says.
- The scheduled action picks every customer invoice of that date, posted or not.
