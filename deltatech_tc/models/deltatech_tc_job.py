import json
import logging
from datetime import timedelta
from urllib.parse import urlparse

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import SQL

_logger = logging.getLogger(__name__)

# A callback is a method name stored in the database, so it must never be able to
# reach arbitrary ORM methods (``unlink``, ``write``, ``sudo``...). Only methods
# carrying this prefix may be called back, which makes "callable from a job" an
# explicit, greppable property of the method rather than an accident.
CALLBACK_PREFIX = "_tc_"

ALLOWED_SCHEMES = ("http", "https")
ALLOWED_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD")
# HTTP methods whose repetition changes nothing on the device.
SAFE_HTTP_METHODS = ("GET", "HEAD")

# Queue tuning. Each value can be overridden with the ``ir.config_parameter`` of the
# same name (prefixed ``deltatech_tc.``); see ``_tc_param``.
DEFAULT_CLAIM_TIMEOUT_MINUTES = 15  # a claimed job without result is considered lost after this
DEFAULT_MAX_ATTEMPTS = 3  # offers of a retry-safe job before it is failed
DEFAULT_DONE_TTL_DAYS = 30
DEFAULT_ERROR_TTL_DAYS = 90
DEFAULT_PENDING_TTL_HOURS = 0  # 0 = pending jobs never expire


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
    attempt_count = fields.Integer(
        string="Attempts",
        readonly=True,
        copy=False,
        help="How many times the job was handed to the station. A retry-safe job whose "
        "result never arrives is offered again, up to the configured limit.",
    )
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
    def _tc_param(self, key, default):
        """Integer queue setting from ``ir.config_parameter`` ``deltatech_tc.<key>``."""
        raw = self.env["ir.config_parameter"].sudo().get_param(f"deltatech_tc.{key}")
        try:
            return max(0, int(raw)) if raw not in (None, False, "") else default
        except (TypeError, ValueError):
            return default

    def _tc_is_retry_safe(self):
        """May this job run a second time if its result was lost?

        The station keeps no record of what it already executed, so offering a lost
        job again means running it again. That is harmless for a ping or an HTTP
        ``GET``, and wrong for anything with an effect outside Odoo: a declaration
        uploaded to ANAF, a ``POST`` that moves a sorting line. Unknown types are
        therefore unsafe; feature modules extend this for their read-only types.
        """
        self.ensure_one()
        if self.job_type == "ping":
            return True
        if self.job_type == "http_request":
            return (self.payload_dict().get("method") or "GET").upper() in SAFE_HTTP_METHODS
        return False

    @api.model
    def _claim_for_station(self, station, limit=10):
        """Claim the pending jobs queued for this station and mark them ``claimed``.

        Jobs are addressed to one station (``station_id`` is required), so a
        station must never pick up the queue of another station of the same
        company: the payload may target a device only that workstation reaches.

        The claim locks the rows (``FOR UPDATE SKIP LOCKED``). A plain ``search``
        followed by ``write`` let two simultaneous polls read the same pending rows
        and both run the job: exactly what happens when a second workstation is
        installed by copying the profile, key included.
        """
        self._requeue_lost_jobs(station)
        self.flush_model(["station_id", "state"])
        self.env.cr.execute(
            SQL(
                """
                SELECT id FROM %s
                 WHERE station_id = %s AND state = 'pending'
                 ORDER BY id
                 LIMIT %s
                   FOR UPDATE SKIP LOCKED
                """,
                SQL.identifier(self._table),
                station.id,
                limit,
            )
        )
        jobs = self.sudo().browse(row[0] for row in self.env.cr.fetchall())
        for job in jobs:
            job.write(
                {
                    "state": "claimed",
                    "claimed_at": fields.Datetime.now(),
                    "attempt_count": job.attempt_count + 1,
                }
            )
        return jobs

    @api.model
    def _requeue_lost_jobs(self, station):
        """Deal with this station's jobs claimed long ago and never answered.

        Without this a job whose result was lost (agent restarted, network down
        between execution and ``/tc/result``) stayed ``claimed`` for ever, and so
        did the document waiting for it.

        * retry-safe job: back to ``pending``, so the next poll runs it again; after
          ``max_attempts`` offers it fails instead of looping;
        * any other job: left ``claimed``. It may well have run, and a late result
          must still be accepted. A manager decides, with the job's **Retry** button.
        """
        timeout = self._tc_param("claim_timeout_minutes", DEFAULT_CLAIM_TIMEOUT_MINUTES)
        if not timeout:
            return self.browse()
        stale = fields.Datetime.now() - timedelta(minutes=timeout)
        self.flush_model(["station_id", "state", "claimed_at"])
        self.env.cr.execute(
            SQL(
                """
                SELECT id FROM %s
                 WHERE station_id = %s AND state = 'claimed' AND claimed_at < %s
                 ORDER BY id
                   FOR UPDATE SKIP LOCKED
                """,
                SQL.identifier(self._table),
                station.id,
                stale,
            )
        )
        lost = self.sudo().browse(row[0] for row in self.env.cr.fetchall())
        max_attempts = self._tc_param("max_attempts", DEFAULT_MAX_ATTEMPTS) or DEFAULT_MAX_ATTEMPTS
        requeued = self.browse()
        for job in lost.filtered(lambda j: j._tc_is_retry_safe()):
            if job.attempt_count >= max_attempts:
                job.write(
                    {
                        "state": "error",
                        "done_at": fields.Datetime.now(),
                        "error": self.env._(
                            "No result from the station after %(count)s attempts. Check the station, then use Retry.",
                            count=job.attempt_count,
                        ),
                    }
                )
            else:
                job.write({"state": "pending", "claimed_at": False})
                requeued |= job
        return requeued

    def action_retry(self):
        """Put the job back in the queue: after an error, or when it is stuck ``claimed``.

        For a job that is not retry-safe this runs it again on the station, which is
        the point of doing it by hand. Hence no ``sudo``: only whoever may write jobs
        (the Terrabit Connect manager) can do it, including over RPC.
        """
        self.check_access("write")
        self.filtered(lambda j: j.state in ("error", "claimed")).write(
            {
                "state": "pending",
                "result": False,
                "error": False,
                "claimed_at": False,
                "done_at": False,
                "attempt_count": 0,
            }
        )
        return True

    @api.model
    def _gc_jobs(self):
        """Daily cleanup (cron): old finished jobs go, stale pending ones may expire.

        Results can carry documents (an SPV download, an HTTP body) and the table
        otherwise only grows. Errors are kept longer: they are the trace of a real
        problem. Expiring pending jobs is off by default, so a declaration queued
        on Friday for a workstation switched off until Monday still goes through.
        """
        now = fields.Datetime.now()
        done_days = self._tc_param("done_ttl_days", DEFAULT_DONE_TTL_DAYS)
        error_days = self._tc_param("error_ttl_days", DEFAULT_ERROR_TTL_DAYS)
        pending_hours = self._tc_param("pending_ttl_hours", DEFAULT_PENDING_TTL_HOURS)
        Job = self.sudo().with_context(active_test=False)
        expired = Job.browse()
        if pending_hours:
            expired = Job.search(
                [("state", "=", "pending"), ("create_date", "<", now - timedelta(hours=pending_hours))]
            )
            expired.write(
                {
                    "state": "error",
                    "done_at": now,
                    "error": self.env._(
                        "No station picked the job up within %(hours)s hours - expired.",
                        hours=pending_hours,
                    ),
                }
            )
        old = Job.browse()
        for state, days in (("done", done_days), ("error", error_days)):
            if not days:
                continue
            limit = now - timedelta(days=days)
            # jobs finished before `done_at` existed on every path count from their creation
            old |= Job.search(
                [
                    ("state", "=", state),
                    "|",
                    ("done_at", "<", limit),
                    "&",
                    ("done_at", "=", False),
                    ("create_date", "<", limit),
                ]
            )
        count = len(old)
        old.unlink()
        _logger.info("Terrabit Connect queue cleanup: %s jobs deleted, %s expired.", count, len(expired))
        return True

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
