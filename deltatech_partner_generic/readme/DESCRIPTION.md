Shops, points of sale and imports often record sales for customers who are not
identified, under one generic partner. That partner must not end up on a real
invoice, must not be paid through the wrong journals and must not be edited by
mistake, since it is reachable from every sales document. This module declares the
generic partner of each company and enforces these rules.

**Generic partner per company**: set in **Invoicing > Configuration > Settings**,
section **Customer Invoices**, field **Generic Partner**. The module creates a company
contact named *Generic* that can be chosen there, or any other contact can be used.
The setting only declares the partner: it is not filled in automatically on sales
orders or invoices.

**No validated invoice for the generic partner**: a customer invoice or credit note
whose customer or delivery address is the generic partner (or one of its contacts)
cannot be validated. The error names the invoice and asks for the real customer.
Drafts stay allowed, so the flows that go through the generic partner (Point of Sale,
eCommerce, imports) keep working. Vendor bills and journal entries are not affected.

**Restricted payment journals**: bank and cash journals ticked as **Generic
Restriction** (on the journal form, next to the journal type, and as an optional
column in the journal list) are not proposed when a payment is made for the generic
partner, either in a new payment or in the **Register Payment** wizard opened from an
invoice. Only bank and cash journals are proposed, and the default journal is always
an allowed one.

**Protect the generic partner**: tick **Protect Generic Partner** in the same setting
to prevent accidental changes. The contact form then shows a warning banner, and any
change, archiving or deletion is refused when saving. The protection is off by
default. Users who have to change the partner are given the **Generic Partner:
Editor** group; Settings administrators already have it. Writes made by Odoo itself
(chatter, activities, portal signup tokens, geolocation) stay allowed, as do automated
flows running with elevated rights.

These accounting restrictions used to live in the separate module
`deltatech_generic_partner_restriction`, which is now an empty transition module
depending on this one.
