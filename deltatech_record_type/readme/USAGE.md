1. Create record types from one of these menus, depending on the document you want to type:
   - **Sales > Configuration > Order Types**
   - **Purchase > Configuration > Order Types**
   - **Accounting > Configuration > Invoice Types** (or **Accounting > Customer Invoices** menu area)
2. On a record type, set:
   - **Allowed Users**: only these users will see/be able to select this type (leave empty for everyone).
   - **Routes**: stock routes to apply when this type is used (visible with multi-step/advanced routing enabled).
   - **Default Values**: a list of fields (on the sale order / purchase order / invoice) that get auto-filled with a fixed value whenever a record of this type is created.
3. The **Type** field then shows up on the Sales Order, Purchase Order and Invoice form views (next to the partner) — but only once at least one type is defined for that document, otherwise the field stays hidden.
4. In **Settings > Sales > Quotations & Orders**, the option **Can confirm orders without record type** controls whether a sales order can be confirmed if no type is selected.
