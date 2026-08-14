## 19.0.1.0.0

- Migration to Odoo 19.0.
- Security group moved from `category_id` to `privilege_id` (`product.res_groups_privilege_product`) and from `users` to `user_ids`, following the Odoo 19 `res.groups` refactoring.
- `_check_can_update_message_content` now handles the message recordset instead of a single record.
