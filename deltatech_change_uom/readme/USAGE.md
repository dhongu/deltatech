Install only **Change Unit of measure** (`deltatech_change_uom`): its dependency **UoM Domain by
Reference** (`deltatech_uom_domain`) is installed with it. Both folders of the download must be in
your addons path; then use **Apps → Update Apps List** and search without the "Apps" filter.

Enable **Units of Measure** in **Inventory → Configuration → Settings**. Administrators can change
units right away; give other users the **Allow to change unit of measure** group (user form, in
developer mode).

The module **relabels the unit, it does not convert quantities**: a line of 4.50 Units becomes
4.50 m³, at the same price and amount. Use it when the figures were already right in the new unit and
only the unit was chosen wrongly. When the product has not been invoiced yet, standard Odoo lets you
change the unit directly on the product form.

1. **Open the action** — open the product (**Inventory → Products → Products**), click the ⋮ button next
   to its name and choose **Change Uom**. The action is on the product form, not on a product variant.

   ![Action menu (⋮) of the product form, with the Change Uom action](static/description/en/01_produs_actiune_schimba_um.png)

2. **Choose the units** — in the **Change Uom** wizard, choose the new **Unit of Measure** (1), from
   any unit tree, and the **Default Purchase Unit** (2), among the units convertible to the new one;
   a purchase unit that no longer fits is cleared. Click **Apply** (3).

   ![Change Uom wizard: Unit of Measure (1), Default Purchase Unit (2) and Apply (3)](static/description/en/02_asistent_schimba_um.png)

3. **Check the product** — the smart buttons show the same figures in the new unit (on hand 2.50 m³,
   sold 2.00 m³, purchased 4.50 m³). In the **Purchase** tab, the vendor line is in m³ at the same
   price, and **Default Purchase Unit** (1) is m³. Prices are not recalculated: check that the vendor
   price is the price per new unit.

   ![Product after the change: vendor line in m³ and Default Purchase Unit m³ (1)](static/description/en/03_produs_dupa_schimbare.png)

4. **Purchase orders** — the received and billed purchase order line moved from Units to m³; quantity,
   received, billed, unit price and amount are unchanged. Lines in the old purchase unit move to the
   new purchase unit, so the order, the receipt and the bill stay in the same unit.

   ![Received and billed purchase order, line in m³](static/description/en/04_comanda_achizitie_dupa.png)

5. **Posted invoices** — the posted customer invoice line is in m³, at the same price and amount
   (2.00 m³, 2,900.00). This is the case standard Odoo refuses. The invoice is not reposted, and
   documents already sent outside Odoo (e-invoicing, tax reports) keep the old unit. The **Unit**
   column is optional on invoice lines: show it from the column menu.

   ![Posted customer invoice, line in m³](static/description/en/05_factura_client_dupa.png)

6. **Stock moves** — the receipt (4.50) and the delivery (2.00) are in m³, with the same quantities.

   ![Moves history of the product, in m³](static/description/en/06_miscari_stoc_dupa.png)

No journal entry is created and no amount or account changes; only the unit on the lines is replaced,
also on posted entries and in locked periods.
