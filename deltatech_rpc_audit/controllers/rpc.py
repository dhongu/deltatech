# ©  2024-2026 Terrabit
# See README.rst file on addons root folder for license details

import logging
import time
import xmlrpc.client
from collections.abc import Mapping, Sequence

from odoo.http import dispatch_rpc, request, route
from odoo.modules.registry import Registry
from odoo.tools import SQL, config, frozendict

# Reuse the helpers from core so this override stays a faithful copy.
# In Odoo 19 the RPC controller moved out of ``base`` into the dedicated
# ``rpc`` module and was split into ``XMLRPC`` and ``JSONRPC`` controllers.
from odoo.addons.rpc.controllers import RPC_DEPRECATION_NOTICE, _check_request
from odoo.addons.rpc.controllers.json2 import WebJson2Controller
from odoo.addons.rpc.controllers.jsonrpc import JSONRPC
from odoo.addons.rpc.controllers.xmlrpc import XMLRPC, dumps

_logger = logging.getLogger("odoo.rpc.audit")

# Logger of the core JSON-RPC controller, used to emit the deprecation notice
# the same way core does when we re-declare the ``/jsonrpc`` route, so
# behaviour stays identical to the stock module.
_core_json_logger = logging.getLogger("odoo.addons.rpc.controllers.jsonrpc")

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

# Calls on ``/json/2`` that are the platform talking to itself, not an integration.
# Odoo.sh drives the scheduler through ``/json/2/ir.cron/acquire_job`` in a tight
# loop -- several hundred calls an hour on a live database -- and logging those
# would bury the handful of lines the audit exists for. Skipped by (model, method)
# rather than by IP, because the address the platform calls from is not stable.
_JSON2_SKIP = frozenset(
    {
        ("ir.cron", "acquire_job"),
    }
)


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
                SQL(
                    "SELECT key, value FROM ir_config_parameter WHERE key IN %s",
                    (_ENABLED_PARAM, _IGNORE_PARAM),
                )
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


def _log_json2_call(model, method, ids, kwargs):
    """Log one ``/json/2/<model>/<method>`` call.

    The modern endpoint carries the model and the method in the URL and takes the
    record ids apart from the keyword arguments, so there is nothing to unpack the
    way the legacy services need. The line keeps the same fields as the legacy one
    so a single grep still finds every call, and adds ``via=json2`` to tell the two
    endpoints apart -- which is the whole point while integrations are being moved
    across.
    """
    if not _logger.isEnabledFor(logging.INFO):
        return
    if (model, method) in _JSON2_SKIP:
        return

    db = request.db
    enabled, ignore_ips = _settings(db)
    if not enabled:
        return

    ip = _client_ip()
    if ip in ignore_ips:
        return

    args = dict(kwargs)
    if ids:
        args = {"ids": list(ids), **args}
    _logger.info(
        "RPC ip=%s db=%s uid=%s model=%s method=%s args=%s via=json2",
        ip,
        db,
        request.env.uid,
        model,
        method,
        _trim(args),
    )


class AuditJson2(WebJson2Controller):
    """Audit layer over the modern ``/json/2`` endpoint.

    The legacy endpoints are deprecated in Odoo 19, so integrations will move here.
    Without this the audit trail would go quiet exactly as that happens -- the
    calls would still be served, just no longer visible.

    The route is inherited rather than re-declared: an empty ``@route()`` keeps
    core's own path, auth and readonly resolution, so only the logging is added.
    """

    @route()
    def web_json_2_rpc(
        self,
        __model__: str,
        __method__: str,
        ids: Sequence[int] = (),
        context: Mapping = frozendict(),
        **kwargs,
    ):
        _log_json2_call(__model__, __method__, ids, kwargs)
        return super().web_json_2_rpc(__model__, __method__, ids=ids, context=context, **kwargs)


class AuditXMLRPC(XMLRPC):
    """Audit layer over the core XML-RPC controller.

    ``_xmlrpc`` is the shared helper called by both ``/xmlrpc/<service>`` and
    ``/xmlrpc/2/<service>``; overriding it here covers both legacy endpoints
    without re-declaring the routes (so error handling stays exactly as core).
    """

    def _xmlrpc(self, service):
        data = request.httprequest.get_data()
        params, method = xmlrpc.client.loads(data, use_datetime=True)
        _log_rpc_call(service, method, params)
        result = dispatch_rpc(service, method, params)
        return dumps((result,))


class AuditJSONRPC(JSONRPC):
    """Audit layer over the core JSON-RPC controller."""

    @route("/jsonrpc", type="jsonrpc", auth="none", save_session=False)
    def jsonrpc(self, service, method, args):
        """Method used by client APIs to contact Odoo."""
        _core_json_logger.warning(RPC_DEPRECATION_NOTICE, "odoo.addons.rpc.controllers.jsonrpc")
        _check_request()
        _log_rpc_call(service, method, args)
        return dispatch_rpc(service, method, args)


class RPC(AuditXMLRPC, AuditJSONRPC):
    """Composite controller mirroring the core ``rpc.RPC`` class.

    ``AuditJson2`` stays out of it on purpose: core keeps ``/json/2`` in a
    controller of its own, and mirroring that keeps the override next to what it
    overrides.
    """
