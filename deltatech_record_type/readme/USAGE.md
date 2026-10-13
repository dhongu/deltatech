Before you start, check the *Configuration* section: types are defined once, then offered on
sales orders, purchase orders and invoices. A type is a classification, a source of default values
and (for sales) stock routes. It has no direct accounting effect.

**Step 1 — Define an order type**

Go to **Sales → Configuration → Order Types** and click **New**. Fill in **Name** (for example
"Wholesale sale"), keep **Model** = *Sales Order* (it is filled in automatically when you open
the list from this menu), and optionally set **Allowed Users**, **Routes** and **Company**.
Empty **Allowed Users** means the type is available to everyone; the restriction applies to
sales orders only. Empty **Company** means all companies.

Do not change **Model** after creation: the default values are tied to fields of the chosen
model. For another document, create a new type.

![Order type form for sales orders](https://apps.odoocdn.com/apps/assets/19.0/deltatech_record_type/record_type_sale_form.png)

**Step 2 — Add default values**

On the **Default Values** tab add one line per field to pre-fill: choose the **Field** (for
example *Customer Reference* or *Payment Terms*) and fill in **Field Value**:

- text and selection values go **between apostrophes**, for example `'Wholesale order'`;
- booleans are `True` or `False`;
- numbers are written without apostrophes, for example `5`;
- relational fields (customer, payment terms, warehouse, journal) are picked in the **Related** column.
  Odoo pre-fills the first record found, so check it and change it if needed.

The **Field Type** column is filled in automatically for relational, char, selection, integer
and boolean fields. For float, monetary, date, datetime and long text fields, check it manually
(for example `12.5` or `'2026-12-31'`). Many2many and one2many fields cannot be used.

![Default values of a type](https://apps.odoocdn.com/apps/assets/19.0/deltatech_record_type/record_type_default_values.png)

Purchase types are defined in **Purchase → Configuration → Order Types**, and invoice types in
**Accounting → Configuration → Invoicing → Invoice Types**. The screen is the same; only the
target document differs.

![List of order types](https://apps.odoocdn.com/apps/assets/19.0/deltatech_record_type/record_type_list.png)

**Step 3 — Pick the type on a sales order**

Go to **Sales → Orders → Quotations → New**. The **Order Type** field appears before the
customer and offers only the types you are allowed to use. When you pick one, its default values
are applied to the order. Default values apply at selection time, so existing documents are
not changed. The field becomes read-only after confirmation or cancellation.

The **Journal** (invoice journal) is also visible on the order, in **Other Info → Invoicing**.

![Sales order with the type selected and default payment terms applied](https://apps.odoocdn.com/apps/assets/19.0/deltatech_record_type/record_type_sale_order.png)

**Step 4 — Confirm the order**

Click **Confirm**. If types exist for sales and the order has none, users without the exception
right get the message *"You do not have the rights to confirm an order without specifying an
Order Type."* Orders from the website are not blocked. Quotations accepted or paid by the customer
in the portal are confirmed normally and stay without a type, so pick the type on the quotation
before sending it if you need it for reporting.

When the order lines have no route of their own, procurement uses the **routes of the type**;
the effect shows on the generated transfers.

![Blocking message when confirming without a type](https://apps.odoocdn.com/apps/assets/19.0/deltatech_record_type/record_type_confirm_blocked.png)

**Step 5 — Pick the type on a purchase order**

Go to **Purchase → Orders → Requests for Quotation → New**. **Order Type** appears before the
vendor, and **Journal** in **Other Info**, after **Fiscal Position**. The list of types is not
filtered by allowed users. The type can be changed only while the order is a draft. Confirmation
follows the same rule as for sales, without the website exception.

Set **Journal** manually or through a default value of the type. When you click **Create Bill**,
the vendor bill is issued in the order's journal and follows its sequence. If **Journal** is
empty, the default purchase journal is used.

![Purchase order with type and journal](https://apps.odoocdn.com/apps/assets/19.0/deltatech_record_type/record_type_purchase_order.png)

![Vendor bill generated in the order's journal](https://apps.odoocdn.com/apps/assets/19.0/deltatech_record_type/record_type_vendor_bill_journal.png)

**Step 6 — Pick the type on an invoice**

Go to **Accounting → Customers → Invoices → New**. **Invoice Type** is in **Other Info**,
**Invoice** group, after **Sales Team**, and is editable only in draft. The type is optional on
invoices: posting does not check it. It exists only on customer invoices and credit notes, and it is
not copied from the sales order, so choose it on the invoice. Its default values apply when picked.

![Invoice with the type selected](https://apps.odoocdn.com/apps/assets/19.0/deltatech_record_type/record_type_invoice.png)

**Step 7 — Filter, group and analyze**

The **Order Type** column is available (optional) in the lists of sales orders, purchase orders
and invoices. In search you get an **Order Type** field and an **Order Type** group-by. Sales and
purchase reports expose the type as a dimension through **Custom Group**.

![Sales orders grouped by type](https://apps.odoocdn.com/apps/assets/19.0/deltatech_record_type/record_type_group_by.png)
