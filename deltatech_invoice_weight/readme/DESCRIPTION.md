Shows the total net and gross weight of the goods on sale orders, purchase orders
and invoices, and prints the weights on the invoice, for transport documents and
customer requests.

**Weights on documents.** Adds **Gross Weight** and **Net Weight** to sale orders
and purchase orders (in a new **Weight** tab) and to invoices and bills (in the
*Other Info* tab, after *Fiscal Position*). Invoices also get a **Package Weight**
field, filled in by hand.

**Calculated when the document is created.** The totals are the sum over the
product lines: the line quantity is converted to the product unit of measure and
multiplied by the product weight. The gross weight comes from the standard
**Weight** of the product and is converted to kg when weights are configured in
pounds. The net weight comes from the product net weight field
(`l10n_ro_net_weight`); this module does not show that field on the product form,
modules such as the Romanian stock localization do.

**Editable totals.** The weight fields are ordinary fields: you can correct them
by hand on the document.

**Weight on the printed invoice.** When the invoice has a gross weight, the gross
and net weights are printed under the payment communication.

## Configuration

Set the **Weight** of each product on the product form, *Inventory* tab. The
weight unit (kilograms or pounds) is chosen in *Inventory > Configuration >
Settings*.

## Limitations

- The weights are calculated only once, when the order or invoice is created.
  Lines added or changed later do not update them.
- The weights are not available in *Accounting > Reporting > Invoice Analysis*
  or in the sales and purchase analysis reports.
- On the printed invoice the net weight is labelled "New weight".
