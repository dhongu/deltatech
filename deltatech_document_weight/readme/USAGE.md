Open **Sales ‣ Configuration ‣ Settings** and look for **Weights on documents**:

- **Weights on quotations** (on by default): the quotation / sales order report.
- **Weights on invoices** (off by default): the customer invoice.
- **Only the gross weight** (off by default): on the printed documents shows only the gross weight, per line and in total, without the net weight and the volume.
- **Copy weights to all variants** (off by default): when the weight, the volume or the net weight is set on a product template, it is written on all its variants, and on the variants created on demand (dynamic attributes), for example when the product is added to a quotation line through the product configurator. Odoo already writes the weight and the volume of a template on all its variants; this option adds the net weight and the variants created on demand.

The print options are set per company.

In the lines of a quotation, sales order or customer invoice, the **Gross weight** column is available in the optional columns selector (the icon at the right of the header). It shows the estimated gross weight of the line quantity, so it can be used for the transport estimate before printing.
