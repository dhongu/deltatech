# ©  2024-2026 Terrabit
# See README.rst file on addons root folder for license details

import logging
import time
import xmlrpc.client

from odoo.http import dispatch_rpc, request, route
from odoo.modules.registry import Registry
from odoo.tools import config

# Reuse the helpers from core so this override stays a faithful copy.
from odoo.addons.base.controllers.rpc import RPC, _check_request, dumps

_logger = logging.getLogger("odoo.rpc.audit")

# Maximum length of the serialized arguments written to the log line.
_MAX_ARGS_REPR = 500

# System Parameters (work on Odoo.sh, where the config file is not editable).
# On a self-hosted server the config-file keys ``rpc_audit_enabled`` and
# ``rpc_audit_ignore_ips`` are honored as well; either source can disable.
_ENABLED_PARAM = "rpc_audit.enabled"
_IGNORE_PARAM = "rpc_audit.ignore_ips"

# Short cache so we do not open a cursor on every single RPC call.
_SETTINGS_TTL = 60  # seconds
_settings_cache = {}  # db -> (expiry_ts, {"enabled": bool, "ignore_ips": set})

_FALSY = {"0", "false", "no", "off", ""}


def _as_bool(value, default):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in _FALSY


def _client_ip():
    """Return the real client IP.

    Behind a reverse proxy (nginx on a self-hosted box, the Odoo.sh edge) the
    ``remote_addr`` is the proxy IP. The real client is the first entry of the
    ``X-Forwarded-For`` header. We read the header directly so it works
    regardless of the ``proxy_mode`` server option.
    """
    httprequest = request.httprequest
    forwarded_for = httprequest.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return httprequest.remote_addr or "?"


def _settings_from_config():
    enabled = _as_bool(config.get("rpc_audit_enabled"), True)
    raw_ips = config.get("rpc_audit_ignore_ips") or ""
    ignore_ips = {ip.strip() for ip in raw_ips.split(",") if ip.strip()}
    return enabled, ignore_ips


def _settings_from_param(db):
    """Read enabled flag + ignore list from ir.config_parameter (cached)."""
    now = time.time()
    cached = _settings_cache.get(db)
    if cached and cached[0] > now:
        return cached[1]
    enabled = True
    ignore_ips = set()
    try:
        with Registry(db).cursor() as cr:
            cr.execute(
                "SELECT key, value FROM ir_config_parameter WHERE key IN %s",
                ((_ENABLED_PARAM, _IGNORE_PARAM),),
            )
            rows = dict(cr.fetchall())
        enabled = _as_bool(rows.get(_ENABLED_PARAM), True)
        raw_ips = rows.get(_IGNORE_PARAM) or ""
        ignore_ips = {ip.strip() for ip in raw_ips.split(",") if ip.strip()}
    except Exception:  # never let auditing break a real RPC call
        enabled, ignore_ips = True, set()
    result = {"enabled": enabled, "ignore_ips": ignore_ips}
    _settings_cache[db] = (now + _SETTINGS_TTL, result)
    return result


def _settings(db):
    """Effective settings, merging the config file and System Parameters."""
    enabled, ignore_ips = _settings_from_config()
    if db:
        param = _settings_from_param(db)
        enabled = enabled and param["enabled"]
        ignore_ips = ignore_ips | param["ignore_ips"]
    return enabled, ignore_ips


def _trim(value):
    text = repr(value)
    if len(text) > _MAX_ARGS_REPR:
        return text[:_MAX_ARGS_REPR] + "...(truncated)"
    return text


def _log_rpc_call(service, rpc_method, params):
    # Cheapest guard first: if the logger is muted (e.g. raised above INFO via
    # log_handler), do no work at all -- not even repr() of the arguments.
    if not _logger.isEnabledFor(logging.INFO):
        return

    db = params[0] if service == "object" and params else None
    enabled, ignore_ips = _settings(db)
    if not enabled:
        return

    ip = _client_ip()
    if ip in ignore_ips:
        return

    # The "object" service carries the ORM call we usually care about:
    # params = [db, uid, password, model, method, args, kwargs]
    # ``args`` holds the positional payload (e.g. ids, domain, vals) while
    # ``kwargs`` carries the keyword payload (e.g. fields, limit, context) that
    # a plain ``method=execute_kw`` log line would otherwise drop.
    if service == "object" and len(params) >= 5:
        uid = params[1]
        model, orm_method = params[3], params[4]
        orm_args = params[5] if len(params) > 5 else []
        orm_kwargs = params[6] if len(params) > 6 else {}
        _logger.info(
            "RPC ip=%s db=%s uid=%s model=%s method=%s args=%s kwargs=%s",
            ip,
            db,
            uid,
            model,
            orm_method,
            _trim(orm_args),
            _trim(orm_kwargs),
        )
    else:
        # common / db services: never log credentials, only the RPC method.
        _logger.info("RPC ip=%s service=%s method=%s", ip, service, rpc_method)


class RPC(RPC):
    """Audit layer over the core XML-RPC / JSON-RPC controller."""

    def _xmlrpc(self, service):
        _check_request()
        data = request.httprequest.get_data()
        params, method = xmlrpc.client.loads(data, use_datetime=True)
        _log_rpc_call(service, method, params)
        result = dispatch_rpc(service, method, params)
        return dumps((result,))

    @route("/jsonrpc", type="json", auth="none", save_session=False)
    def jsonrpc(self, service, method, args):
        _check_request()
        _log_rpc_call(service, method, args)
        return dispatch_rpc(service, method, args)
