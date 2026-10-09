# Bug review — Category Group

Review date: 2026-10-02. Target version: Odoo 19.

## CATEGORYGROUP-001 — P1: Category manager group implies user IDs as group IDs

- **Status:** Fixed in 19.0.0.0.6. `security.xml` adds `base.user_root` and `base.user_admin` as members (`user_ids`) of the group instead of implying their IDs as groups; the 19.0.0.0.6 migration removes the wrong `res_groups_implied_rel` links of this group in existing databases.
- **Location:** security/security.xml, category_group_manager.implied_ids.
- **Trigger:** Install/update the addon or assign its Manage category groups group.
- **Actual behavior:** implied_ids receives (4, ref('base.user_root')) and (4, ref('base.user_admin')). These references return res.users IDs, but implied_ids targets res.groups. Numeric ID collisions link unrelated groups; if no group with that number exists, the relation fails. This also does not assign the intended manager group to those users.
- **Evidence:** Compared actual XML commands with base/data/res_users_data.xml, which declares both references as res.users, and base/models/res_groups.py, which declares implied_ids as a res.groups Many2many. Reference model mismatch is explicit; exact accidentally implied groups depend on database ID allocation and were not guessed.
- **Impact:** Incorrect group inheritance changes access membership, potentially grants unintended permissions, and can prevent installation in a database without matching group IDs.
- **Suggested fix:** Use group XML IDs for implications and a proper user/group membership relation if explicit user membership is intended. Audit/remove existing unintended implication links during upgrade.
- **Validation needed:** Clean installation, upgraded database with different ID allocation, manager membership and effective implied permissions; verify intended administrators receive the group without inheriting unrelated groups.

## Review limitations

All eligible Python/XML source and access CSV were read. Native model/reference declarations compared; no database installation, security mutation or integration tests executed.
