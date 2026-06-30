This module logs external **XML-RPC** (`/xmlrpc`, `/xmlrpc/2`) and **JSON-RPC**
(`/jsonrpc`) calls, so you can audit which integration calls which model and
method, and from where.

For each call to the `object` service it logs the client IP, database, user id,
model, method and a trimmed representation of both the positional arguments
(`args`) and the keyword arguments (`kwargs`, e.g. `fields`, `limit`,
`context`), under the logger `odoo.rpc.audit`. Credentials are never logged.

The real client IP is read from the `X-Forwarded-For` header, so calls behind a
reverse proxy (nginx, the Odoo.sh edge) are not all attributed to the proxy IP
(e.g. `10.0.0.2`), independently of the `proxy_mode` server option.

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
