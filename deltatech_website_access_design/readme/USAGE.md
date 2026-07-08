This module restricts the Contacts, Sales, and Invoicing/Payables backend menus to a dedicated **Access Partners, Sale, Invoice** group, instead of leaving them visible to every internal user. This is meant for setups where a web designer or other limited-access internal user should only work on the Website app, without seeing customer, sales, or accounting data.

1. The `Access Partners, Sale, Invoice` group is created automatically on install and is granted by default to the Administrator and root users.
2. To let another internal user see Contacts, Sales, and Invoicing menus, go to Settings > Users & Companies > Users, open their profile, and add them to the **Access Partners, Sale, Invoice** group.
3. Internal users who are not in this group will no longer see the Contacts, Sales, or Invoicing (Receivables/Payables) menus, while still being able to use the Website app.
