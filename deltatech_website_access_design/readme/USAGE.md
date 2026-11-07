## Check the access group after installation

Open **Settings > Users & Companies > Groups** (developer mode) and search for
*Access Partners, Sale, Invoice*. The **Users** tab lists every internal user
that existed at installation, so nobody lost the Contacts, Sales or Invoicing
menus.

![Group Access Partners, Sale, Invoice, Users tab: the internal users existing at installation, each with their login and role](static/description/en/01_grup_acces_utilizatori.png)

The **Menus** tab lists the menus reserved to the group: Invoicing/Customers,
Invoicing/Vendors, Contacts and, when the Sales app (`sale_management`) is installed, Sales.

![Group Access Partners, Sale, Invoice, Menus tab: Invoicing/Customers, Invoicing/Vendors and Contacts](static/description/en/02_grup_acces_meniuri.png)

## Set up the web designer

1. In **Settings > Users & Companies > Users**, open the designer's user. In the
   **Access Rights** tab, set **Website** to **Restricted Editor** and save.
2. In the group *Access Partners, Sale, Invoice*, **Users** tab, remove the
   designer and save.

![User form of the designer, Access Rights tab: role User, Website Restricted Editor, Sales and Accounting No](static/description/en/03_utilizator_designer.png)

The designer now opens the website with the **Editor** button and edits the
pages, without seeing Contacts, Sales or Invoicing > Customers / Vendors.

![Website opened by the designer, with the Editor button at the top left](static/description/en/04_website_designer.png)

Internal users created after the installation are not in the group: add each one
who needs these menus.
