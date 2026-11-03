Hides the back-office menus for partners, sales and invoices from users who
should only work on the website, such as a web designer. The module does not
grant any website rights: give the designer the usual website access rights
yourself, then this module keeps the commercial menus out of their view.

**Dedicated access group.** The module creates the group *Access Partners, Sale,
Invoice*. On installation only the administrator (and the superuser) are members.

**Restricted menus.** The following menus are reserved to that group, replacing
the groups they had before:

- **Contacts** (the Contacts app);
- **Sales** (the Sales app);
- **Invoicing > Customers**;
- **Invoicing > Vendors**.

Every user who is not in the group, the internal salespeople and accountants
included, no longer sees these menus. Add each user who still needs them to the
group in **Settings > Users & Companies > Users**, or in
**Settings > Users & Companies > Groups**, group *Access Partners, Sale, Invoice*.

The module hides menus only. It does not change record rules or access rights,
so the records stay reachable through other menus, links or smart buttons.

## Limitations

- Odoo adds groups to a menu when the module that defines it is updated. After
  an update of Contacts, the Contacts menu is visible again to all internal
  users, until this module is updated too.
- Uninstalling the module deletes the group but does not restore the original
  groups on the four menus.
