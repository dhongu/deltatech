This module has no UI — it works passively once installed, writing one log line per external XML-RPC/JSON-RPC call to the `odoo.rpc.audit` logger (client IP, database, user id, model, method, and trimmed arguments). Read the log through your usual server log / log aggregator.

- It is enabled by default. To disable without uninstalling, set either:
  - the config-file key `rpc_audit_enabled = False` (self-hosted), or
  - the System Parameter `rpc_audit.enabled` to a falsy value (`0`/`false`/`no`/`off`) — works on Odoo.sh, no restart needed.
- To silence noisy sources (health checks, monitoring probes) without disabling auditing entirely, list their IPs in:
  - the config-file key `rpc_audit_ignore_ips` (comma-separated), or
  - the System Parameter `rpc_audit.ignore_ips` (comma-separated) — both sources are merged.
- On a self-hosted server you can also mute the logger by log level instead, e.g. `--log-handler=odoo.rpc.audit:WARNING`.
