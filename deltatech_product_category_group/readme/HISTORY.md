## 19.0.1.0.6 (2026-10-02)

- Fix `responsible_determination`: the user group was written with a raw SQL `UPDATE` that bypassed the ORM cache, so `user_group_id` stayed empty in the same transaction. Both fields are now written with `write()`; the count query stays SQL. The test now checks balancing between two users, the category inherited from the parent and the pickings left unchanged (already assigned / not ready).

## 19.0.1.0.5 (2026-09-29)

- Own module icon, instead of the generic gears it had.
