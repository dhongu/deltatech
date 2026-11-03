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
- the state of the order.

Groupings by category, product, order, state, company and month, and a *Done*
filter, are available. The report opens on done orders of the previous month.

## Configuration

Set the **Cost Category** on the product categories of your components in
*Inventory > Configuration > Products > Categories*. Components whose
category has no cost category are included in the total consumed value but in none of
the split columns.

## Limitations

- The 20% indirect cost rate used for *Value production* and *Actually Price*
  is fixed in the report and cannot be configured.
- On 20.0 the report still uses the manufacturing order states of older Odoo
  versions: *Current* finds only draft orders, *In Production*, *Ready to
  Produce* and *Picking Exception* find nothing, *Waiting Goods* shows every
  confirmed order whatever the component readiness, and orders in progress or
  to close have no state label.
- On 20.0, when the unit of the manufacturing order differs from the unit of
  the product (for example 2 dozen of a product measured in units), *Qty Plan*
  and *Val Plan* divide the quantity by the unit factor instead of converting
  it.
