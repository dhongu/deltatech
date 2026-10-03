# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## TYPE-001 — P1: Default-value records do not inherit parent company restrictions

- **Status:** Fixed in 19.0.1.1.18 — `security/record_type_security.xml` adds a multi-company rule on `record.type.default.values` through `record_type_id.company_id`, and `write()` checks write access on the target record type when `record_type_id` changes. The ACLs (full CRUD for internal users on both models) are unchanged. Covered by tests in `tests/test_company_rules.py`.
- **Location:** security/ir.model.access.csv; security/record_type_security.xml; models/record_type.py, record.type.default.values.
- **Trigger:** An internal user restricted to company A searches/reads/writes default-value records belonging to a company-B record type through ORM/RPC.
- **Actual behavior:** The parent record.type has a global company rule, but record.type.default.values has no rule of its own. Its ACL grants every internal user full read/write/create/delete. Neither the child fields nor mutation methods enforce access to record_type_id.
- **Evidence:** Full child model, ACL and security source inspected. Only model_record_type is named in the company rule; no child rule/server check exists. Parent ACL/rules do not automatically propagate to a separate model. No live cross-company write executed.
- **Impact:** Users can inspect, alter or delete another company's default values. When that company's users subsequently choose the type, its onchange applies the modified values to their sales, purchases or invoices.
- **Suggested fix:** Apply parent-company rules to child default records and restrict configuration writes to an appropriate administrative role; validate parent access when creating/reassigning children.
- **Validation needed:** Parent inaccessible but child searched/modified directly, cross-company child creation/reassignment, shared types and authorized configuration maintenance.

## TYPE-002 — P2: Every internal user has full rights on record types and default values

- **Status:** Open. Found on 2026-10-03 while fixing TYPE-001.
- **Location:** security/ir.model.access.csv (`access_record_type`, `access_record_type_default_values`: `base.group_user`, 1,1,1,1); models/account_move.py, models/sale.py, models/purchase.py (default values applied with `safe_eval(default_value.field_value)` on type change).
- **Trigger:** An internal user without sales/purchase/accounting configuration rights creates or edits a record type or its default values through RPC (the menus are under the configuration menus, but the ACL is not restricted).
- **Actual behavior:** Both models grant read/write/create/unlink to every internal user. Default values are arbitrary field name/value pairs applied by the onchange when another user picks the type on a sale order, purchase order or invoice; `user_ids` (allowed users) and routes are editable as well. TYPE-001 added the company rules but explicitly left the ACLs unchanged.
- **Evidence:** source inspection of the ACL, the security XML and the onchanges applying the default values; no RPC call executed.
- **Impact:** A regular user can change configuration that silently pre-fills documents of other users in the same company (for example payment terms, journal or bank account on invoices) and widen or narrow who may use a type.
- **Suggested fix:** Keep read access for internal users and restrict write/create/unlink to a configuration role (for example sales/purchase managers or `base.group_system`, or a dedicated group).
- **Validation needed:** Internal user without configuration rights: read allowed, write/create/unlink refused; managers can still maintain types and default values; selecting a type still applies its defaults.

## Review limitations

All eligible Python/XML source manually reviewed: type/default field and reference computation, onchange defaults, mandatory-type checks and portal/payment exceptions, procurement route propagation, report SQL extensions, settings, domains, ACLs and company rules. Source finding only; no Odoo cross-company mutation, report SQL or integration test execution.
