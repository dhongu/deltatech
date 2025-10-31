# Deltatech Product Chatter

Restrict deletion (and emptying) of chatter messages on Product Template and Product Variant unless the user belongs to a dedicated security group.

## What it does
- Blocks deleting product-related chatter messages from the UI (the chatter "Delete" action).
- Blocks direct record deletions of `mail.message` linked to products (e.g., via ORM/RPC, scripts, or third‑party modules) when the user lacks the group.

## How it works
- UI delete path: overrides the product models’ `_check_can_update_message_content` to require the special group before allowing message content updates (including clearing the body to "delete").

## Security
- Group: `Delete Product Chatter Messages`
  - XML ID: `deltatech_product_chatter.group_delete_product_chatter`
  - Assign this group only to trusted users who are allowed to delete or edit chatter messages on products.

## Usage
1. Install the module.
2. Assign the group to authorized users: Settings → Users & Companies → Users → Access Rights → "Delete Product Chatter Messages".
3. Test on a product form’s chatter:
   - Without the group: deletion/edit of messages is blocked with an error.
   - With the group: deletion/edit behaves as usual.

## Compatibility
- Odoo 17.0
- Depends on `product` and `mail`.

## Notes
- Restriction applies only to messages on `product.template` and `product.product`. Other models are unaffected.
- No data is modified beyond preventing unauthorized deletions/edits of product chatter messages.
