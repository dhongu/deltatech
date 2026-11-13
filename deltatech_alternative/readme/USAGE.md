## Adding Alternative Codes to a Product

1. Open **Sales > Products > Products** (or **Inventory > Products > Products**).
2. Select or create the product you want to enrich.
3. Go to the **Alternative** tab on the product form.
4. Click **Add a line** and enter the alternative code in the **Code** column. Spaces are
   part of the code: `366 200 05 01` stays one code.
5. Repeat for every additional code. Use the drag handle to reorder them in the tab.
6. Tick **Hide** on any code you do not want included in the combined **Alternative Code**
   field. A hidden code still finds the product.
7. Save.

Creating, editing and deleting codes requires the *Inventory / User* access right; other
internal users can see the codes but not change them.

![Alternative tab of the Engine oil filter product: three codes in the Code column, 366 200 05 01, FLT-2041 and OLD-0457; only OLD-0457 has Hide ticked](static/description/en/01_tab_coduri_alternative.png)

## Alternative Code and Used For on the Product

On the **General Information** tab, the **Alternative Code** field shows the visible codes
separated by `; `, in the order in which they were added. **Used For** is a free-text note on
what the product can be used for.

You can also type in **Alternative Code**: on a product without codes the text becomes the
first code, and on a product with exactly one code it replaces that code. On a product with
several codes or with a hidden code the change is not saved; edit the codes on the
**Alternative** tab instead.

![General Information tab of the product: Alternative Code 366 200 05 01; FLT-2041 and Used For Diesel 2.0 TDI](static/description/en/02_produs_cod_alternativ.png)

Both fields are also columns of the product list. In the list search, type a code and choose
**Search Alternatives for** to filter the products that have it.

![Product list filtered on Alternatives 366: one row, Engine oil filter, FU-1001, with Alternative Code 366 200 05 01; FLT-2041 and Used For Diesel 2.0 TDI](static/description/en/03_lista_produse.png)

## Searching by Alternative Code

1. Go to **Purchase > Configuration > Settings**, section **Products**, tick
   **Alternative Search** and save.
2. Open any product selection field, for example on a Sales Order line, a Purchase Order
   line or a transfer.
3. Type the code, or part of it. The matching product appears in the dropdown after the
   products whose name or internal reference match the same text.

![Purchase settings, Products section: Alternative Search ticked, with Code Before Name and Show Stock in Dropdown below](static/description/en/04_setari_cautare.png)

![New quotation: 366 200 typed in the Product field of a line, and the dropdown suggests Engine oil filter, FU-1001, found by its alternative code](static/description/en/05_cautare_comanda.png)

The same settings section has two options for the product dropdown:

- **Code Before Name** shows the classic `[code] name` instead of the Odoo 19 layout with the
  internal reference muted on the right;
- **Show Stock in Dropdown** shows, muted on the right, the quantity on hand of storable
  products.

## Alternative Code on Orders and Transfers

The **Alternative Code** column is available (optional, hidden by default) on Sales Order
lines, Purchase Order lines, transfer operations and the **Detailed Operations** window. To
show it:

1. Open a Sales Order (**Sales > Orders > Quotations**), a Purchase Order
   (**Purchase > Orders > Requests for Quotation**) or a transfer
   (**Inventory > Operations > Transfers > Deliveries** or **Receipts**).
2. In the lines list, click the optional-columns button (on the right of the column headers).
3. Tick **Alternative Code** to display the column.

The column is read-only and shows the visible codes of the product on each line.

![Quotation lines with the Alternative Code column displayed: 366 200 05 01; FLT-2041 on the FU-1001 Engine oil filter line](static/description/en/06_comanda_coloana_cod.png)

![Delivery order, Operations tab, with the Alternative Code column displayed on the product line](static/description/en/07_transfer_coloana_cod.png)

## Splitting Codes Entered on One Line

Codes imported or typed on one line and separated by `;` or `,` can be split into one code
per line by the scheduled action **Alternative: Split multi-code records**, inactive by
default. In debug mode, open **Settings > Technical > Automation > Scheduled Actions**,
then turn on **Active** for a daily run or click **Run Manually** once. Each run processes up
to 5,000 lines; codes the product already has are not created again, and spaces never split a
code.

![Scheduled action Alternative: Split multi-code records, Active turned off, with model.split_multi_codes() in the Code tab](static/description/en/08_actiune_planificata.png)
