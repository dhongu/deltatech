1. Open *Inventory > Operations > Transfers > Receipts*. The **Amount** column shows the valuation
   value of each receipt and the total at the bottom. A receipt that is not validated yet is worth 0.00.

   ![Receipts list: the Amount column shows 0.00 for the Ready receipt, 400.00 and 1,300.00 for the Done ones, with the total 1,700.00](static/description/en/01_receptii_valoare.png)

2. The same column in *Deliveries* shows the cost of the goods that left the stock, not the sales price.

   ![Deliveries list: the Amount column shows 320.00 and 365.00 for the Done deliveries, with the total 685.00](static/description/en/02_livrari_valoare.png)

3. Open the top product category (*Inventory > Configuration > Products > Product Categories*), set
   **Income Account**, **Expense Account**, **Costing Method** and **Inventory Valuation**, then set
   **Stock Account** and save. Saving a new **Stock Account** copies all these settings to every
   subcategory.

   ![The Mărfuri (goods) category: Stock Account 371000, Income Account 707000 and Costing Method Average Cost (AVCO) highlighted](static/description/en/03_categorie_parinte_conturi.png)

4. Check a subcategory: it now has the same accounts, costing method and inventory valuation.

   ![The Becuri (bulbs) subcategory, under Mărfuri / Electrice: Stock Account 371000 and Costing Method Average Cost (AVCO) copied from Mărfuri](static/description/en/04_subcategorie_conturi_copiate.png)

5. When you change another setting of the top category, copy the settings again with the gear icon >
   **Propagate Accounts** (developer mode).

   ![The gear menu of the category form, with the Propagate Accounts action highlighted](static/description/en/05_actiune_propagare_conturi.png)

6. On a new category, choosing a **Parent Category** fills in the accounting settings of the parent.

   ![A new category with Parent Category selected: Stock Account and Costing Method filled in from the parent](static/description/en/06_categorie_noua_setari_parinte.png)

7. A user who is not in the **Change Product Price** group cannot change the **Cost** of a product that
   has quantity on hand: saving shows an **Access Error**.

   ![The product form of a product with 80.00 on hand: the Access Error dialog says the user is not allowed to change the cost price](static/description/en/07_cost_refuzat_fara_drept.png)

8. Manage who may change the cost in *Settings > Users & Companies > Groups* > **Change Product Price**
   (developer mode). The administrator is in the group by default.

   ![The Change Product Price group, Users tab, with the Administrator as its only member](static/description/en/08_grup_modificare_cost.png)

The copy to subcategories overwrites their settings, empty values included: set exceptions on a
subcategory after the propagation. The cost of products without stock and the automatic cost updates
(for example the average cost recomputed at a receipt) are not restricted.
