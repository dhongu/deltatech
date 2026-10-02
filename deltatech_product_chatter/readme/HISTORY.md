## 19.0.1.0.2 (2026-10-02)

- Block direct deletion of product chatter messages (`mail.message.unlink()` through ORM/RPC/scripts) for users outside the security group, as the description promised: only the edit/"Delete" action of the chatter was guarded before. Sudo is not blocked, so deleting a product still removes its messages. Tests added.

## 19.0.1.0.1

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.0

- Migration to Odoo 19.0.
- Security group moved from `category_id` to `privilege_id` (`product.res_groups_privilege_product`) and from `users` to `user_ids`, following the Odoo 19 `res.groups` refactoring.
- `_check_can_update_message_content` now handles the message recordset instead of a single record.
