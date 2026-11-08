1. Install the module, or on Odoo Online import the zip from **Apps > Import Module**
   (Custom plan, developer mode). There is nothing to configure; for the vendor search, the
   products need their vendors in the **Purchase** tab of the product form.
2. Open **Invoicing > Customers > Invoices** and type a product name, or part of it, in the search
   bar. Two new suggestions appear: **Search Product for: ...** and **Search Vendor for: ...**.

   ![Invoices list with TEST Ergonomic typed in the search bar; the suggestions include Search Product for: TEST Ergonomic (highlighted) and Search Vendor for: TEST Ergonomic](static/description/en/01_cautare_dupa_produs.png)

3. Choose **Search Product**: the list keeps only the invoices that have the product on at least
   one line. The search uses the product name, its internal reference or its barcode.

   ![Invoices list filtered by Product: TEST Ergonomic, showing the invoices of TEST Contoso Interiors Ltd and TEST Northwind Builders Ltd](static/description/en/02_facturi_filtrate_produs.png)

4. Remove the facet, type a vendor name and choose **Search Vendor**: the list keeps the invoices
   with products bought from that vendor, whatever the product.

   ![Invoices list filtered by Vendor: TEST Office, showing three invoices with products supplied by TEST Office Supply Ltd](static/description/en/03_facturi_filtrate_furnizor.png)

Both criteria are available in every invoice list: customer invoices and credit notes, vendor
bills and refunds. They can be combined with each other and with the standard filters.
