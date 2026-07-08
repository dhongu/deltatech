This module works together with `deltatech_partner_generic`, which lets you configure a "generic" customer (via the system parameter `sale.partner_generic_id`) used for anonymous/walk-in sales.

1. Go to **Accounting > Configuration > Journals**, open a Bank or Cash journal, and tick **Generic Restriction** (`restriction` field, shown next to Type in both the list and form view).
2. When registering a payment for the generic partner (the one configured in `sale.partner_generic_id`), only Bank/Cash journals that do **not** have Generic Restriction enabled will be offered in the payment's journal selection — journals marked as restricted are hidden for that partner.
3. No action is required for regular (non-generic) partners; the restriction only applies when the payment's customer is the configured generic partner.
