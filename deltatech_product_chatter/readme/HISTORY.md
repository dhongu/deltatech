## 20.0.1.0.3 (2026-10-22)

- Listed on Odoo Apps as *Product Chatter Protection* (was *Product Chatter*), with the same title on the Apps banner.
  The technical name `deltatech_product_chatter` does not change.

## 20.0.1.0.2 (2026-10-15)

- Block direct deletion of product chatter messages (`mail.message.unlink()` through ORM/RPC/scripts) for users outside the security group, as the description promised: only the edit/"Delete" action of the chatter was guarded before. Sudo is not blocked, so deleting a product still removes its messages. Tests added (the "other models" test gives its user read access on journal entries when `account` is installed).

## 20.0.1.0.1

- Migration to Odoo 20.0. No functional changes: the `_check_can_update_message_content`
  hook and the `res.groups` fields (`privilege_id`, `user_ids`) are unchanged in 20.0.
- Added tests for the product chatter restriction.

## 19.0.1.0.1

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.0

- Migration to Odoo 19.0.
- Security group moved from `category_id` to `privilege_id` (`product.res_groups_privilege_product`) and from `users` to `user_ids`, following the Odoo 19 `res.groups` refactoring.
- `_check_can_update_message_content` now handles the message recordset instead of a single record.
