Suppliers and customers often name a product by its manufacturer's part number, which can differ from your internal reference. This module adds that number to products and makes it searchable in the product list.

- **MPN field**: The product form shows an *MPN* text field (help text: Manufacturer Part Number). It is optional and has no uniqueness or format check.
- **Search by MPN**: The search bar of the product list gains an *MPN* search, so typing a part number finds the products that carry it. The module adds no MPN search to the variants list or to product fields on documents.
- **Optional columns**: The product list and the product variants list can show an *MPN* column. It is hidden by default and appears when ticked in the optional columns menu.
- **One value per product**: The MPN belongs to the product, not to a variant, so all variants show the same value. The module does not add the field to the variant form.

It depends only on *Products* (`product`) and adds no menu, setting or security group, so anyone who can edit a product can edit its MPN. The module only stores and displays the number: it does not copy it to orders, invoices, reports or the website.
