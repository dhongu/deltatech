Lets a company keep the **Sales Price** of its products in a currency other than
its accounting currency, for example prices in EUR in a company that keeps its
books in RON. Sales orders and pricelists convert the price to their own currency
at the rate of the day.

**Price List Currency on the company.** Adds the **Price List Currency** field on
the company form, under **Currency**. The currency of the product **Sales Price**
becomes this currency for all the products of the company. Products shared
between companies use the price list currency of the main company.

**Conversion in pricelists and sales.** When a pricelist or a sales order is in
another currency, the sales price is converted from the price list currency with
the standard Odoo currency rates. The **Cost** of products stays in the company
currency.

## Configuration

Go to *Settings > Users & Companies > Companies*, open the company and set
**Price List Currency**. To keep the sales prices in the company currency, set
it to the same currency as **Currency**.

## Limitations

- The setting applies to the whole company: all products use the same price list
  currency; it cannot be chosen per product.
- On installation every company gets EUR as **Price List Currency**. In a company
  whose currency is not EUR, the existing sales prices are then read as EUR
  amounts until the field is changed.
