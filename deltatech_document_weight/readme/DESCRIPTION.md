Prints the net weight, the gross weight and the volume of the goods on the quotation and on the customer invoice: under the name of each product, and in total below the amounts.

The values are estimates: the quantity of the line, converted to the unit of measure of the product, multiplied by the weight and the volume of the product. Lines whose product has no weight and no volume print nothing, and the totals block is left out when all the totals are 0.

The net weight is the `l10n_ro_net_weight` field of the product. The module declares it exactly as `l10n_ro_stock` and `l10n_ro_stock_base` do, so it works with either of them or without them; if one of them is installed the field is the same, and shown only once on the product form.

It does not change `deltatech_invoice_weight`, which stores the totals on the document.
