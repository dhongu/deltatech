# Confirmed bugs — 2026-10-03

## PRODCHATTER-001 — P2: direct message CRUD bypasses special group

Only product _check_can_update_message_content is guarded. Native mail.message.write/unlink do not call that document hook, and ordinary internal users have message CRUD ACL subject to native message/document access. An otherwise authorized caller can edit/delete an accessible product message through direct ORM/RPC without the special group. The addon therefore protects the UI update-content route, not its stated product-message deletion restriction across entry points. Enforce the intended restriction on message CRUD as well, preserving legitimate document deletion/system cleanup semantics.

Evidence: complete addon import graph and native mail.message write/unlink/access/ACL read. No mail.message override is loaded (commented import only). Source-supported bypass subject to native access; database RPC/permission test unexecuted.

## Limits

UI route hook composes native tracking/comment restrictions; group is not a general permission grant. No source fixes or external messages. No database/browser tests executed.
