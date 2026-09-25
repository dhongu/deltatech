This module logs external RPC calls, so you can audit which integration calls
which model and method, and from where. It covers both the legacy endpoints —
**XML-RPC** (`/xmlrpc`, `/xmlrpc/2`) and **JSON-RPC** (`/jsonrpc`) — and the
modern **`/json/2/<model>/<method>`**.

Covering the modern endpoint matters because the legacy ones are deprecated in
Odoo 19: as integrations move across, an audit that watched only the old
endpoints would go quiet without anything failing to say so.

For each call it logs the client IP, database, user id, model, method and a
trimmed representation of the arguments, under the logger `odoo.rpc.audit`.
Credentials are never logged. Lines from the modern endpoint carry an extra
`via=json2`, so the two can be told apart during a migration while a single grep
still finds every call.

Calls to `/json/2/ir.cron/acquire_job` are skipped: on Odoo.sh that is the
platform driving the scheduler in a tight loop, and logging it would bury the
handful of lines the audit exists for.

The client IP is the `remote_addr` resolved by the Odoo server. Behind a reverse
proxy (nginx, the Odoo.sh edge) run the server with `proxy_mode` -- always on for
Odoo.sh -- so calls are not all attributed to the proxy IP (e.g. `10.0.0.2`). The
`X-Forwarded-For` header is set by the caller and is not trusted: it is only
appended to the line as `xff=...`, never used to decide whether a call is skipped.

The module can be turned on/off without uninstalling it, via the config-file
key `rpc_audit_enabled` (self-hosted) or the System Parameter
`rpc_audit.enabled` (works on Odoo.sh, no rebuild). When the `odoo.rpc.audit`
logger is muted above INFO, the module does no work at all.

Noisy IPs (health checks, monitoring) can be skipped via:

- the config-file key `rpc_audit_ignore_ips` (self-hosted), or
- the System Parameter `rpc_audit.ignore_ips` (works on Odoo.sh),

both comma separated and merged together.

It is meant as a lightweight diagnostic / audit tool; the web client UI is not
affected, since it uses a different endpoint.
