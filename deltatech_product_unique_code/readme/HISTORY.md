## 19.0.1.0.0

- [PORT] ported from 18.0 to Odoo 19.0 (`res.groups.users` renamed to `user_ids`, dropped `category_id`)
- [IMP] "no new duplicates" policy: validation moved from `@api.constrains` to `create()`/`write()` overrides — only values that actually change are validated, so products carrying historical duplicates can be cleaned up (archived, corrected one field at a time, cleared or renamed) by regular users; new or changed values must still be unique
- [FIX] fixing both `default_code` and `barcode` in the same save through the product template no longer fails on the stale (pre-write) barcode value: the check runs after `super()`, once the template inverse fields have propagated to the variants
- [IMP] `active` removed from the checked fields: archiving a duplicate is allowed (archived products are part of the uniqueness check anyway, so archiving never frees a code)
