# History

## 19.0.1.2.2 (2026-09-25)

- Security: the client IP is now `remote_addr`, no longer the first entry of
  `X-Forwarded-For`. That entry is set by the caller (nginx only appends to the
  header), so anyone with an API key could send the address of an `ignore_ips` entry
  and drop out of the audit on `/xmlrpc`, `/jsonrpc` and `/json/2`, or log a false IP.
  Behind a reverse proxy run the server with `proxy_mode` (always on for Odoo.sh):
  core then resolves `remote_addr` from the entry the trusted proxy added.
- The raw header is still written at the end of the line as `xff=...`, as
  information only; it is never used to skip a call.

## 19.0.1.2.1 (2026-08-25)

- Fix: coerce a `None` XML-RPC result to `False` before marshalling. A handful of
  ORM methods (e.g. `account.move.line.reconcile()` when there is nothing to
  reconcile) legitimately return `None`; core's own marshaller is built with
  `allow_none=False`, so the call was crashing with `TypeError: cannot marshal
  None unless allow_none is enabled` instead of returning a normal result.

## 19.0.1.2.0 (2026-08-14)

- Add: the modern `/json/2/<model>/<method>` endpoint is audited too. The legacy
  endpoints are deprecated in Odoo 19, so integrations will move across -- and until
  now the audit trail would have gone quiet exactly as that happened: the calls still
  served, just no longer visible, with nothing failing to say so.
- The line keeps the same fields as the legacy one, so a single grep still finds every
  call, and adds `via=json2` to tell the two endpoints apart while integrations are
  being moved.
- `/json/2/ir.cron/acquire_job` is skipped: Odoo.sh drives the scheduler through it in
  a tight loop, and logging that would bury the handful of lines the audit exists for.
  Skipped by (model, method), because the address the platform calls from is not stable
  enough to skip by IP.
- The route is inherited rather than re-declared, so core keeps deciding the path, the
  authentication and whether the call is readonly; only the logging is added.

## 19.0.1.1.0 (2026-06-30)

- Port to Odoo 19. The core RPC controller moved out of ``base`` into the
  dedicated ``rpc`` module and was split into ``XMLRPC`` / ``JSONRPC``; the
  audit layer now overrides ``rpc.XMLRPC`` / ``rpc.JSONRPC`` (composite ``RPC``
  controller) and depends on ``rpc`` instead of ``base``. Behaviour is
  unchanged.

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
