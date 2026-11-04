Enable pricelists first: *Sales > Configuration > Settings*, **Pricing** section, tick **Pricelists**
and save.

1. Go to *Sales > Products > Pricelists* and open a pricelist. Click the **Pricelist Lines** button at
   the top of the form.

   ![Pricelist form with the Pricelist Lines button highlighted (1) and the rules in the Sales Prices tab](static/description/en/01_buton_linii_lista_preturi.png)

2. The list shows all the rules of this pricelist: product, minimum quantity, price and validity
   period. The **Price** column shows the fixed price; for *Discount* or *Formula* rules open the rule
   to see the price. For category or all-products rules the **Products** column is empty; show the
   optional **Apply On** column.

   ![The rules of the pricelist opened from the button, with the breadcrumb highlighted (1)](static/description/en/02_lista_linii_preturi.png)

3. Type a product name or code in the search bar (1) and choose **Search Product for: ...** (2).
   Category, pricelist and currency (with several active currencies) searches and the standard group
   by options are also available.

   ![The search bar (1) with the text Laptop and the Search Product proposal (2)](static/description/en/03_cautare_produs.png)

4. Click a line to open the rule, change for instance **Min Qty** or **Fixed Price** and save. **New**
   creates a rule already linked to the current pricelist. Start and end dates include the time: set the end
   time to 23:59 so the rule applies for the whole last day.

   ![A pricelist rule opened from the list: Min Qty (1) and Fixed Price (2)](static/description/en/04_formular_regula.png)

5. To let a user manage prices without Sales Administrator rights, activate the developer mode, go to
   *Settings > Users & Companies > Groups*, open **Permit pricelist editing** (1) and add the user in
   the **Users** tab (2) with **Add a line** (3). In developer mode the group can also be ticked on the
   user form, **Access Rights** tab, **Extra Rights** section.

   ![The Permit pricelist editing group (1), Users tab (2) and Add a line (3)](static/description/en/05_grup_utilizatori.png)

   The **Access Rights** tab (1) shows the rights granted: read, write, create and delete on
   pricelists and pricelist rules.

   ![The Access Rights tab (1) of the group: full rights on Pricelist and Pricelist Rule](static/description/en/06_grup_drepturi_acces.png)
