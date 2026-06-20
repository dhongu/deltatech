import json
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DeltatechTcJob(models.Model):
    """A unit of work Terrabit Connect executes locally on behalf of a company.

    Cloud queue: Odoo creates ``pending`` jobs; the station claims them through
    ``/tc/poll`` (they become ``claimed``), runs them locally and reports back
    through ``/tc/result`` (``done``/``error``). Result processing is delegated
    to the :meth:`_process_result` hook, which feature modules extend per
    ``job_type``.

    Feature modules add their job types with ``selection_add`` on ``job_type``.
    """

    _name = "deltatech.tc.job"
    _description = "Terrabit Connect Job"
    _order = "id desc"

    name = fields.Char(compute="_compute_name")
    station_id = fields.Many2one("deltatech.tc.station", required=True, ondelete="cascade", index=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    job_type = fields.Selection(
        selection=[("ping", "Ping")],
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

    @api.depends("job_type")
    def _compute_name(self):
        for rec in self:
            label = dict(self._fields["job_type"].selection).get(rec.job_type, rec.job_type or "")
            rec.name = f"#{rec.id} {label}"

    def payload_dict(self):
        self.ensure_one()
        try:
            return json.loads(self.payload) if self.payload else {}
        except ValueError:
            return {}

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
        """Hook extended by feature modules per ``job_type``.

        Default: no-op for ``ping``. Feature modules (ANAF messages, fiscal,
        labels) override this to turn the station's result into business records.
        """
        return True
