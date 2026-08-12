import json
import logging
from urllib.parse import urlparse

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# A callback is a method name stored in the database, so it must never be able to
# reach arbitrary ORM methods (``unlink``, ``write``, ``sudo``...). Only methods
# carrying this prefix may be called back, which makes "callable from a job" an
# explicit, greppable property of the method rather than an accident.
CALLBACK_PREFIX = "_tc_"

ALLOWED_SCHEMES = ("http", "https")
ALLOWED_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD")


class DeltatechTcJob(models.Model):
    """A unit of work Terrabit Connect executes locally on behalf of a company.

    Cloud queue: Odoo creates ``pending`` jobs; the station claims them through
    ``/tc/poll`` (they become ``claimed``), runs them locally and reports back
    through ``/tc/result`` (``done``/``error``). Result processing is delegated
    to the :meth:`_process_result` hook, which feature modules extend per
    ``job_type``.

    Two job types ship here: ``ping`` (round-trip check) and ``http_request``,
    which has the station call a device reachable only inside the customer's
    network. Feature modules add device-specific types with ``selection_add`` on
    ``job_type``.
    """

    _name = "deltatech.tc.job"
    _description = "Terrabit Connect Job"
    _order = "id desc"

    name = fields.Char(compute="_compute_name")
    station_id = fields.Many2one("deltatech.tc.station", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    job_type = fields.Selection(
        selection=[("ping", "Ping"), ("http_request", "HTTP request (LAN)")],
        required=True,
        default="ping",
    )
    payload = fields.Text(help='Job parameters, JSON (e.g. {"zile": 30} or {"id": "..."}).')
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("claimed", "Claimed"),
            ("done", "Done"),
            ("error", "Error"),
        ],
        default="pending",
        required=True,
        index=True,
        copy=False,
    )
    result = fields.Text(copy=False)
    error = fields.Text(copy=False)
    claimed_at = fields.Datetime(readonly=True, copy=False)
    done_at = fields.Datetime(readonly=True, copy=False)
    callback_model = fields.Char(
        readonly=True,
        help="Model whose method is called once the station reports the response.",
    )
    callback_res_id = fields.Integer(
        readonly=True,
        help="Record the callback is executed on. 0 calls the method on the model.",
    )
    callback_method = fields.Char(
        readonly=True,
        help=f"Method invoked with the finished job. Must start with '{CALLBACK_PREFIX}'.",
    )

    @api.depends("job_type")
    def _compute_name(self):
        for rec in self:
            label = dict(self._fields["job_type"].selection).get(rec.job_type, rec.job_type or "")
            rec.name = f"#{rec.id} {label}"

    @api.constrains("job_type", "payload")
    def _check_http_payload(self):
        for job in self.filtered(lambda j: j.job_type == "http_request"):
            payload = job.payload_dict()
            url = (payload.get("url") or "").strip()
            if not url:
                raise ValidationError(self.env._("An HTTP job needs a 'url' in its payload."))
            parsed = urlparse(url)
            if parsed.scheme not in ALLOWED_SCHEMES:
                raise ValidationError(
                    self.env._(
                        "Unsupported URL scheme %(scheme)s - only http and https are allowed.",
                        scheme=parsed.scheme or "(none)",
                    )
                )
            if not parsed.netloc:
                raise ValidationError(self.env._("The URL %(url)s has no host.", url=url))
            method = (payload.get("method") or "GET").upper()
            if method not in ALLOWED_METHODS:
                raise ValidationError(self.env._("Unsupported HTTP method %(method)s.", method=method))

    @api.constrains("callback_method")
    def _check_callback_method(self):
        for job in self.filtered("callback_method"):
            if not job.callback_method.startswith(CALLBACK_PREFIX):
                raise ValidationError(
                    self.env._(
                        "The callback method %(method)s must start with '%(prefix)s'.",
                        method=job.callback_method,
                        prefix=CALLBACK_PREFIX,
                    )
                )

    def payload_dict(self):
        self.ensure_one()
        try:
            return json.loads(self.payload) if self.payload else {}
        except ValueError:
            return {}

    # ------------------------------------------------------------------
    # http_request: queue an HTTP call the station performs on the local network
    # ------------------------------------------------------------------
    @api.model
    def _tc_enqueue_http(
        self,
        station,
        url,
        method="GET",
        headers=None,
        body=None,
        timeout=30,
        callback=None,
        company=None,
    ):
        """Queue an HTTP call for the station to perform locally.

        Odoo runs in the cloud while the device (a sorting line, a scale, a PLC)
        answers only inside the customer's network. The station already polls
        Odoo, so routing the call through it keeps the direction outbound-only:
        no inbound port, no VPN, no fixed IP.

        **The allow-list of reachable hosts lives in the agent, not here.** Odoo
        says which URL it wants called; the workstation decides whether it is
        willing to call it. Anything else would turn a compromised Odoo account
        into a foothold inside the customer's network.

        :param callback: ``(record, method_name)`` invoked with the finished job
            once the station reports back. The name must start with ``_tc_``.
        :returns: the created job.
        """
        if not station:
            raise UserError(self.env._("No Terrabit Connect station given for the HTTP job."))
        vals = {
            "station_id": station.id,
            "company_id": (company or station.company_id or self.env.company).id,
            "job_type": "http_request",
            "payload": json.dumps(
                {
                    "url": url,
                    "method": (method or "GET").upper(),
                    "headers": headers or {},
                    "body": body,
                    "timeout": timeout,
                }
            ),
        }
        if callback:
            record, method_name = callback
            if not method_name.startswith(CALLBACK_PREFIX):
                raise UserError(
                    self.env._(
                        "The callback method %(method)s must start with '%(prefix)s'.",
                        method=method_name,
                        prefix=CALLBACK_PREFIX,
                    )
                )
            if not hasattr(record, method_name):
                raise UserError(
                    self.env._(
                        "%(model)s has no method %(method)s.",
                        model=record._name,
                        method=method_name,
                    )
                )
            vals.update(
                {
                    "callback_model": record._name,
                    "callback_res_id": record.id if record else 0,
                    "callback_method": method_name,
                }
            )
        return self.create(vals)

    def response_dict(self):
        """The agent's answer to an ``http_request``: ``{status, headers, body, truncated}``.

        Returns an empty dict when there is no usable result yet, so callers can
        branch on ``status`` without guarding every access.
        """
        self.ensure_one()
        if not self.result:
            return {}
        try:
            data = json.loads(self.result)
        except ValueError:
            _logger.warning("Job %s: result is not valid JSON", self.id)
            return {}
        return data if isinstance(data, dict) else {}

    def response_json(self):
        """The response body parsed as JSON, or ``None`` if it is not JSON."""
        self.ensure_one()
        body = self.response_dict().get("body")
        if body in (None, ""):
            return None
        try:
            return json.loads(body)
        except (ValueError, TypeError):
            return None

    # ------------------------------------------------------------------
    # API used by the controller (called by Terrabit Connect)
    # ------------------------------------------------------------------
    @api.model
    def _claim_for_station(self, station, limit=10):
        """Claim the pending jobs of the station's company and mark them ``claimed``."""
        jobs = self.sudo().search(
            [
                ("company_id", "=", station.company_id.id),
                ("state", "=", "pending"),
            ],
            order="id asc",
            limit=limit,
        )
        jobs.write({"state": "claimed", "station_id": station.id, "claimed_at": fields.Datetime.now()})
        return jobs

    def _store_result(self, status, result=None, error=None):
        """Record the result reported by the station and trigger processing."""
        self.ensure_one()
        if status == "done":
            self.sudo().write(
                {
                    "state": "done",
                    "result": result or "",
                    "error": False,
                    "done_at": fields.Datetime.now(),
                }
            )
            try:
                self.sudo()._process_result()
            except Exception as exc:  # noqa: BLE001 - a processing error must not break the response
                _logger.exception("Processing result of job %s failed", self.id)
                self.sudo().write({"state": "error", "error": str(exc)[:4000]})
        else:
            self.sudo().write({"state": "error", "error": error or "", "done_at": fields.Datetime.now()})
        return True

    def _process_result(self):
        """Turn the station's result into business records.

        Handles the callback of finished ``http_request`` jobs; feature modules
        (ANAF messages, fiscal, labels) extend this per ``job_type``.

        A failing callback is deliberately left to propagate: ``_store_result``
        catches it and flips the job to ``error`` with the message, so swallowing
        it here would hide a real failure.
        """
        for job in self.filtered(lambda j: j.job_type == "http_request" and j.callback_method):
            target = job.env[job.callback_model]
            if job.callback_res_id:
                target = target.browse(job.callback_res_id).exists()
                if not target:
                    _logger.warning(
                        "Job %s: callback target %s,%s no longer exists",
                        job.id,
                        job.callback_model,
                        job.callback_res_id,
                    )
                    continue
            # re-checked at call time: the stored value could have been tampered with
            if not job.callback_method.startswith(CALLBACK_PREFIX):
                raise UserError(
                    self.env._(
                        "Refusing to call %(method)s - callbacks must start with '%(prefix)s'.",
                        method=job.callback_method,
                        prefix=CALLBACK_PREFIX,
                    )
                )
            getattr(target, job.callback_method)(job)
        return True
