# Confirmed bugs — 2026-10-03

## PARTNERDISC-001 — P1: discount permission can be bypassed through write

**Status:** Fixed in 19.0.1.0.3. `write()` refuses a changed discount for users
outside the group (superuser mode excepted); `create()` refuses any nonzero
discount, including a `default_discount` context value. Covered by
`test_write_discount_no_group`, `test_write_same_discount_no_group`,
`test_write_discount_with_group`, `test_create_negative_discount_no_group`.

`models/res_partner.py:16–20` restricts changes using an onchange, while :23–29 checks only partner creation. There is no write override or field-level permission on discount. A user allowed to edit partners but outside group_partner_discount can therefore update an existing partner discount using import/RPC/server-side write, without triggering the onchange. The invoice's recommended discount follows this unauthorized value. Enforce the same permission in write for relevant changes; retain onchange only for immediate UI feedback.

Evidence: all module model/security source reviewed; native partner write inspected and does not implement this custom field's group check. Source-only finding; a non-group user's ORM import/RPC operation was not executed. Standard partner ACLs still apply, so this does not grant general partner access to otherwise unauthorized users.

## Limits

Entire eligible source read; invoice commercial-partner relation and form anchors traced. Creation currently rejects only positive explicit discount values; context defaults/negative values need separate validation. No database/security/browser tests executed.
