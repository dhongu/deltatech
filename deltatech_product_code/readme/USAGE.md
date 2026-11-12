## Setup

1. Create a sequence for the product codes (prefix, for example `ZZ`, and the number of digits) in **Settings → Technical → Sequences** (developer mode), or directly from the **Code Sequence** field of the category with **Create and Edit**.
2. Go to **Inventory → Configuration → Product Categories** and open the category. In the **Products** group choose the **Code Sequence**. For barcodes, tick **Generate Barcode** and choose the **Barcode Source**: *Internal prefix* (a 2-digit prefix between `20` and `29`, plus the digits of the reference or a random number) or *GS1 company prefix* (the next free GTIN-13 in the range of your GS1 prefix; fill in **GS1 Company Prefix**, 6-11 digits; **Free GTIN Codes** shows how many are left). **Barcode Random** is ticked by default: with it ticked the internal barcode is a random number; unticked, it is built from the digits of the reference.

![Product category form, Products group: Code Sequence filled in, Generate Barcode ticked, Barcode Source set to Internal prefix, Prefix Barcode 20 and Barcode Random unticked](static/description/en/01_categorie.png)

## Create a product

1. Go to **Inventory → Products → Products** and click **New**.
2. Enter the name and choose the category configured above. Leave **Reference** and **Barcode** empty.

![New product form, General Information tab: Category set to Piese de schimb, Reference and Barcode fields empty and highlighted](static/description/en/02_produs_nou.png)

3. Save the product. The reference is taken from the category sequence and, if the category asks for it, the barcode is generated (from the reference digits if **Barcode Random** is unticked). A reference typed by hand is kept and no barcode is generated in that case.

![Saved product: the breadcrumb shows [ZZ0001] Filtru de aer, Reference is ZZ0001 and Barcode is 2000000000015, both filled in automatically](static/description/en/03_cod_generat.png)

When you create a product from a sales order line with **Create and edit**, choose the category in the dialog and leave the reference empty: the product gets its code on save. A quick create (name only) has no category, so no code is generated.

## Existing products

Open the product (or select several in the list), open the **Actions** menu (the ⋮ button next to the name) and choose **Force new internal code** to get a new number from the sequence, even if the product already has a reference. **Find Duplicate** lists, from the whole catalog, the products that share their reference with another product (same active status and company), whatever product you ran it from (products without a reference are listed too, if there are at least two). The existing barcode is not changed.

![Actions menu open on product ZZ0001 Filtru de aer, with Find Duplicate and Force new internal code at the end of the list](static/description/en/04_actiuni_produs.png)

Two active products of the same company cannot share a reference: saving is refused with "Internal Reference already exists".
