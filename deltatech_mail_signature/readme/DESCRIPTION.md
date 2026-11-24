One e-mail signature template per company, with fields, generated for every user.

Without it, each user writes their own signature in the preferences: different fonts, a logo pasted
or not, an old phone number. This module keeps **one template per company**, written once in the
Odoo editor with images and fields such as `{{name}}`, `{{job_title}}`, `{{phone}}` or
`{{company_address}}`, and generates from it the signature of every internal user. Everything that
sends the signature of the user (chatter, quotations, invoices, the Mail Client) uses it with no
further work.

**Features**

- Template per company, with the Odoo HTML editor (logo, banner, colors, links).
- Fields filled with the data of the user and of the company: name, job position, e-mail, phone, mobile,
  company name, website, phone, e-mail, address on one line and tax ID.
- A line whose fields are all empty (for example "Tel: {{phone}}" for a user without a phone) is
  not shown at all.
- An unknown field is refused when the template is saved, with the list of valid fields.
- "Generate users' signatures" on the template and "Regenerate my signature" in the preferences of each user.
- The signature is refreshed when the name, job position or phone of the user changes (can be turned off).
- Hand-written signatures are never overwritten by the mass generation or the refresh.
- Values are HTML-escaped, links are checked (no `javascript:`) and the result goes through the HTML
  cleaning of Odoo.
- Images of the template are shared, so they show for recipients outside Odoo.
