Salespeople who analyze sales by customer sometimes need the customer's email address next to the figures. This module adds it to the sales analysis report as a *Partner Email* field.

- **New report field**: *Partner Email* is added to the model behind the sales analysis (`sale.report`) as a text field, read in the same query as the other report columns.
- **Current value**: The field shows the email stored on the customer of the order. Nothing is copied onto the order, so a changed email also appears on past orders.
- **Filter and group**: The email is also part of the grouping of the report query, so the report can be filtered or grouped by it. The module adds no column, filter or menu, so the field is picked by hand, for example in a custom filter or grouping.

The module depends on *Sales* (`sale`) and has no groups or access rules of its own: whoever can open the report can read the emails.
