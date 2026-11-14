Hides the back-office menus for partners, sales and invoices from users who
should only work on the website, such as a web designer. The designer edits the
website with the standard *Website: Restricted Editor* right, without being a
website administrator, and does not see the commercial menus.

**Dedicated access group.** The module creates the group *Access Partners, Sale,
Invoice*. At installation every internal user existing at that moment joins the
group, so nobody loses a menu when the module is installed.

**Restricted menus.** At installation, once, the following menus are reserved
to that group, replacing the groups they had before:

- **Contacts** (the Contacts app);
- **Sales** (the Sales app);
- **Invoicing > Customers**;
- **Invoicing > Vendors**.

An update of this module no longer touches these menus, so groups you add on
them yourself are kept.

**Setting up a web designer.** In **Settings > Users & Companies > Users**, on
the designer's user, set **Website** to *Restricted Editor*: the designer edits
the website pages and content but does not manage the website configuration.
Then remove the designer from the group *Access Partners, Sale, Invoice*, in
**Settings > Users & Companies > Groups** (developer mode), tab **Users**.

The module hides menus only. It does not change record rules or access rights,
so the records stay reachable through other menus, links or smart buttons.

## Limitations

- Internal users created after the installation are not in the group *Access
  Partners, Sale, Invoice*: add each one who needs the Contacts, Sales and
  Invoicing > Customers / Vendors menus to the group.
- Odoo adds groups to a menu when the module that defines it is updated. After
  an update of Contacts, the Contacts menu is visible again to all internal
  users. Remove the group *Internal User* from the menu again, in
  **Settings > Technical > Menu Items**.
- Uninstalling the module gives the four menus back the groups set by their own
  module.
