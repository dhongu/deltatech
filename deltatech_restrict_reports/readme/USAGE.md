## Give each user a report access level

Go to **Settings → Users & Companies → Users**, open the user and, on the **Access Rights** tab,
find the **Restrict Reports** section. In its **Restrict Reports** field choose:

- **Rapoarte Vânzări/Facturi: doar propriile înregistrări** (own records only);
- **Rapoarte Vânzări/Facturi: toate înregistrările** (all records);
- leave it empty for no data at all.

Right after installation nobody has either group, so everybody, administrators included, sees the
two reports empty until the groups are assigned.

![User form, Access Rights tab: Sales is Administrator, Accounting is Invoicing, and in the Restrict Reports section the field is set to own records only](static/description/en/01_grupuri_utilizator.png)

## Sales Analysis

Open **Sales → Reporting → Sales**, switch to the **Pivot** view and group by **Salesperson**.

- With *own records only*, the pivot has a single row, the logged-in user, equal to the total.

![Sales Analysis pivot grouped by Salesperson for Marc Demo: a single row, Marc Demo, 54 Qty Ordered in total](static/description/en/02_analiza_vanzari_proprii.png)

- With *all records*, every salesperson appears, with the same figures for each of them.

![Sales Analysis pivot grouped by Salesperson for a user with all records: Marc Demo 54 and Mitchell Admin 94, total 148 Qty Ordered](static/description/en/03_analiza_vanzari_toate.png)

## Invoice Analysis

Open **Invoicing → Reporting → Management → Invoice Analysis** and group by **Salesperson**. With
*own records only*, only the invoices where the user is the salesperson are counted; invoices of
other salespersons or without a salesperson are left out.

![Invoices Analysis pivot grouped by Salesperson for Marc Demo: a single row, Marc Demo, 84,750.00 Untaxed Amount](static/description/en/04_analiza_facturi_proprii.png)

With *all records*, the other salespersons and the invoices without a salesperson (None) appear
too; the user's own row keeps the same amount.

![Invoices Analysis pivot grouped by Salesperson for a user with all records: Marc Demo 84,750.00, Mitchell Admin 1,275.00 and None 44,299.00, total 130,324.00](static/description/en/05_analiza_facturi_toate.png)

## User without a group

A user in neither group still sees the menus, but both reports open empty, without an access error.

![Invoices Analysis for a user without any report group: no data, Odoo's faded sample chart in the background and its help text for an empty report](static/description/en/06_analiza_facturi_fara_grup.png)

## Notes

- The Sales → Reporting menu requires the **Sales: Administrator** right in standard Odoo; the
  module does not change menu access.
- These two analysis reports, and the **Sold** button on products (computed from Sales Analysis),
  are filtered; orders, invoices, the **Invoiced** button on customers and accounting reports are
  not.
