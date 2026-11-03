The standard manufacturing order shows the cost of components only as a
total. This module splits the value of the consumed components into cost
categories (raw materials, semi-products, packing material) and adds a
production cost analysis that compares the consumed value with the produced
quantity.

**Cost category on product categories.** A **Cost Category** field on the
product category form classifies the products of that category as *Raw
materials*, *Semi-products* or *Packing Material*.

**Costs tab on the manufacturing order.** A **Costs** tab on the
manufacturing order lists the value of the consumed components grouped by
cost category. Only component moves that are done are counted. The **Update**
button refreshes the list.

**Production Cost Analysis.** The *Manufacturing > Reporting > Production
Cost Analysis* report (pivot, list and graph) shows, per manufacturing order:

- the planned quantity and its value at the product cost (*Qty Plan*, *Val
  Plan*), and the produced quantity and value (*Qty Efective*, *Val
  Efective*);
- the consumed value, in total and split by cost category (*Val Consumed*,
  *Val Consumed Raw*, *Val Consumed Packing*, *Val Consumed Semifinish*);
- the production value, equal to the consumed value plus 20% for indirect
  costs (*Value production*), and the resulting unit cost (*Actually Price*)
  next to the product cost (*Price Standard*);
- the state and the readiness of the order.

Filters for current, in-production, done, waiting-goods and ready-to-produce
orders, and groupings by category, product, order, state, company and month,
are available. The report opens on done orders of the previous month.

## Configuration

Set the **Cost Category** on the product categories of your components in
*Inventory > Configuration > Products > Categories*. Components whose
category has no cost category are included in the total consumed value but in none of
the split columns.

## Limitations

- The 20% indirect cost rate used for *Value production* and *Actually Price*
  is fixed in the report and cannot be configured.
