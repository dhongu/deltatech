# Bug review — deltatech_sale_activity_report

Review date: 2026-10-02. Target version: Odoo 19.

## ACTIVITY-001 — P1: Sale activity creation requires an undeclared order stage extension

- **Status:** Open.
- **Location:** models/mail_activity.py, create(); __manifest__.py.
- **Trigger:** Install the addon with its declared sale/data_recycle dependencies, then an internal user schedules an activity on a sale order with no existing daily activity record.
- **Actual behavior:** The create override unconditionally reads sale_order.stage when creating the journal entry. Core sale.order has no stage field; the local provider is deltatech_website_sale_status, absent from the declared dependency closure. There is no optional-field check or exception guard in this override.
- **Evidence:** Executed the actual AST-extracted method with a core-style sale order containing id/state but no stage: AttributeError aborts creation. Read local core sale/order and stage provider manifest/model. No Odoo activity/database creation executed.
- **Impact:** Creating ordinary sales activities can fail and roll back unless an unrelated website status extension is additionally installed.
- **Suggested fix:** Declare the required provider or make stage tracking explicitly optional with a safe field/selection policy.
- **Validation needed:** Install only declared dependencies and create first/subsequent daily activities, then test with the optional stage provider and automated-activity context.

## ACTIVITY-002 — P1: Activity journals bypass sale access scope and allow unrestricted tampering

- **Status:** Open.
- **Location:** security/ir.model.access.csv; models/sale_order_activity_record.py; models/sale_order.py, _log_activity().
- **Trigger:** An ordinary internal user searches/reads/writes sale.order.activity.record directly through ORM/RPC, including records for orders they cannot access.
- **Actual behavior:** The journal model grants all internal users full CRUD, with no company/owner/order-scoped record rule and no field restrictions. Journal entries are created/updated under sudo, so limited users do not prevent global entries. Parent sale.order rules are not inherited by the separate model. Form activity_log readonly and list create=false only affect the UI.
- **Evidence:** Complete model, ACL, manifest, logging hooks and views read. No security XML or authorization/mutation guard is loaded. The journal stores free-text changes/messages, sale state/stage and arbitrary user_id. No live journal read/mutation or access test executed.
- **Impact:** Users can read logged commercial data from hidden orders and alter/delete activity history or attribute fabricated work to another user, compromising confidentiality and reporting integrity.
- **Suggested fix:** Apply explicit company/order access rules and a narrow journal-reader group; restrict create/write/unlink to controlled logging/admin paths and prevent user attribution forgery.
- **Validation needed:** Own/team/other-company order visibility, internal users without sales access, direct log edits/deletion, forged user_id and authorized reporting.

## Review limitations

All eligible source was manually read. The activity reproduction used mock records; ACL/SQL/state findings are source-based. Date-filter percent escaping was checked against the XML loader and excluded as a false positive. No Odoo database/integration tests or live journal/production mutations executed.
