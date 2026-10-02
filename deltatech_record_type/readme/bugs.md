# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## TYPE-001 — P1: Default-value records do not inherit parent company restrictions

- **Status:** Open.
- **Location:** security/ir.model.access.csv; security/record_type_security.xml; models/record_type.py, record.type.default.values.
- **Trigger:** An internal user restricted to company A searches/reads/writes default-value records belonging to a company-B record type through ORM/RPC.
- **Actual behavior:** The parent record.type has a global company rule, but record.type.default.values has no rule of its own. Its ACL grants every internal user full read/write/create/delete. Neither the child fields nor mutation methods enforce access to record_type_id.
- **Evidence:** Full child model, ACL and security source inspected. Only model_record_type is named in the company rule; no child rule/server check exists. Parent ACL/rules do not automatically propagate to a separate model. No live cross-company write executed.
- **Impact:** Users can inspect, alter or delete another company's default values. When that company's users subsequently choose the type, its onchange applies the modified values to their sales, purchases or invoices.
- **Suggested fix:** Apply parent-company rules to child default records and restrict configuration writes to an appropriate administrative role; validate parent access when creating/reassigning children.
- **Validation needed:** Parent inaccessible but child searched/modified directly, cross-company child creation/reassignment, shared types and authorized configuration maintenance.

## Review limitations

All eligible Python/XML source manually reviewed: type/default field and reference computation, onchange defaults, mandatory-type checks and portal/payment exceptions, procurement route propagation, report SQL extensions, settings, domains, ACLs and company rules. Source finding only; no Odoo cross-company mutation, report SQL or integration test execution.
