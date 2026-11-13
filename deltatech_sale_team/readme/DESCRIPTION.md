Companies organized in shops, branches or channels often want each sales team to work on its own documents and to ship from its own warehouse. This module adds a *Team Manager* access level and a default warehouse for every sales team.

- **Team Manager group**: The new *Team Manager* group includes the salesperson group (`sales_team.group_sale_salesman`) and is included in `sales_team.group_sale_salesman_all_leads`. Its members also see the quotations, orders, order lines, sales analysis and invoices of their own sales team, and those with no team. The rule on invoices is read-only.
- **Own team only**: Members of *Team Manager* who do not have `sales_team.group_sale_salesman_all_leads` see only their own team in the list of sales teams.
- **Personal invoices and contacts**: Users of the salesperson group are limited to invoices where they are the salesperson or none is set, and the users of `sales_team.group_sale_salesman_all_leads` see all invoices. Salespeople outside `sales_team.group_sale_manager` also see only contacts assigned to them, unassigned, or their own.
- **Default warehouse**: The sales team form has a *Default Warehouse* field. When a team is chosen on a quotation in the form, the order takes the team's warehouse if there is one.

The module depends on `sales_team`, Invoicing, Inventory and `sale_stock`. The team warehouse is not applied to orders created by import or API. Group rules combine, so a wider rule of another group of the same user still applies.
