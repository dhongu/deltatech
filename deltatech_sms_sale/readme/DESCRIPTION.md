Customers like to hear straight away that their order went through. This module sends them an SMS when a sales order is confirmed and when its confirmation e-mail is sent, using SMS templates you can edit.

- **Confirmation SMS**: When a sales order is confirmed, the customer receives the message of the *SMS Template* chosen under *SMS Sale Order Confirm*, if that option is on and the customer has a phone number.
- **Post SMS**: Each time Odoo sends the order confirmation e-mail, the message chosen under *SMS Sale Order Post* goes out the same way. The settings call this posting the order (help text: from website).
- **Default texts**: Both default templates begin with the company name and state that the order number has been confirmed or posted.
- **Company settings**: Both options sit in the sales settings, are set per company and are on by default. A template is required while its option is on.
- **Template rights**: Sales managers can create, edit and delete the SMS templates of sales orders, and only those.

The module depends on *Sales*, *Sales Teams* and *SMS*. It has no SMS provider of its own: the customer's phone number and the message text go to the SMS service configured in Odoo, and messages are sent immediately, not queued.
