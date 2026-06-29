# History

## 18.0.1.1.0 (2026-06-29)

- Add an on/off switch, so the module can stay installed but idle:
  - config-file key `rpc_audit_enabled` (self-hosted);
  - System Parameter `rpc_audit.enabled` (works on Odoo.sh, no rebuild),
    cached 60s alongside the ignore list.
  Either source can disable; default is enabled.
- Skip all work (including `repr()` of the arguments) when the `odoo.rpc.audit`
  logger is muted above INFO, via an `isEnabledFor` guard.

## 18.0.1.0.0 (2026-06-29)

- Initial release.
- Logs XML-RPC (`/xmlrpc/<service>`, `/xmlrpc/2/<service>`) and JSON-RPC
  (`/jsonrpc`) calls under the logger `odoo.rpc.audit`.
- Resolves the real client IP from the `X-Forwarded-For` header so calls are
  not all attributed to the reverse-proxy IP (e.g. `10.0.0.2`), independently
  of the `proxy_mode` server option.
- For the `object` service logs db / uid / model / method / trimmed args;
  for `common` / `db` services logs only the RPC method (never credentials).
- Optional ignore list (comma separated) to skip noisy IPs (e.g. health
  checks), from two sources merged together:
  - config-file key `rpc_audit_ignore_ips` (self-hosted);
  - System Parameter `rpc_audit.ignore_ips` (works on Odoo.sh), cached 60s.
