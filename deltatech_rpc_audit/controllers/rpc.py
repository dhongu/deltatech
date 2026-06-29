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

# System Parameter holding the comma separated IPs to skip (works on Odoo.sh,
# where the config file is not editable). On a self-hosted server the config
# file key ``rpc_audit_ignore_ips`` is used as well.
_IGNORE_PARAM = "rpc_audit.ignore_ips"

# Short cache so we do not open a cursor on every single RPC call.
_IGNORE_TTL = 60  # seconds
_ignore_cache = {}  # db -> (expiry_ts, frozenset of ips)


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


def _ips_from_config():
    raw = config.get("rpc_audit_ignore_ips") or ""
    return {ip.strip() for ip in raw.split(",") if ip.strip()}


def _ips_from_param(db):
    """Read the ignore list from ir.config_parameter, with a small TTL cache."""
    if not db:
        return set()
    now = time.time()
    cached = _ignore_cache.get(db)
    if cached and cached[0] > now:
        return cached[1]
    value = ""
    try:
        with Registry(db).cursor() as cr:
            cr.execute(
                "SELECT value FROM ir_config_parameter WHERE key = %s",
                (_IGNORE_PARAM,),
            )
            row = cr.fetchone()
            if row and row[0]:
                value = row[0]
    except Exception:  # never let auditing break a real RPC call
        value = ""
    ips = {ip.strip() for ip in value.split(",") if ip.strip()}
    _ignore_cache[db] = (now + _IGNORE_TTL, ips)
    return ips


def _ignored_ips(db):
    return _ips_from_config() | _ips_from_param(db)


def _trim(value):
    text = repr(value)
    if len(text) > _MAX_ARGS_REPR:
        return text[:_MAX_ARGS_REPR] + "...(truncated)"
    return text


def _log_rpc_call(service, rpc_method, params):
    ip = _client_ip()
    db = params[0] if service == "object" and params else None
    if ip in _ignored_ips(db):
        return

    # The "object" service carries the ORM call we usually care about:
    # params = [db, uid, password, model, method, args, kwargs]
    if service == "object" and len(params) >= 5:
        uid = params[1]
        model, orm_method = params[3], params[4]
        orm_args = params[5] if len(params) > 5 else []
        _logger.info(
            "RPC ip=%s db=%s uid=%s model=%s method=%s args=%s",
            ip,
            db,
            uid,
            model,
            orm_method,
            _trim(orm_args),
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
