Product feeds and similar exports need a list of products defined by a rule, so that it stays current when products are added. This module stores such a rule as a reusable *Product List* that other modules read.

- **Rule, not products**: A *Product List* has a name, a product filter (*Products*) and a *Limit*. The filter is built with the domain editor on product variants, and a new list starts with a filter on products that can be sold (`sale_ok`).
- **Limit**: *Limit* is the maximum number of products and defaults to 80. This module does not apply it; the module that uses the list does.
- **Archiving**: A list can be archived, and its form then shows an *Archived* ribbon.
- **Company**: A new list gets the current company. A multi-company rule shows the lists of the active companies and the lists without a company.

The *Product List* menu entry sits in the product catalog menu of Sales. The module depends on `product` and `sale`. All internal users can read the lists, and users of `sales_team.group_sale_salesman` can create, edit and delete them. Modules such as `deltatech_feed` read the filter and the limit.
