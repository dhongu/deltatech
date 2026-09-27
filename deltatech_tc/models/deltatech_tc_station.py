import secrets

from odoo import api, fields, models


class DeltatechTcStation(models.Model):
    """A workstation running Terrabit Connect, registered for a company.

    Cloud model: the station runs Terrabit Connect and always initiates the
    outbound connection to Odoo, authenticating with an API key sent in the
    ``X-Station-Key`` header. Odoo never connects back to the station.

    This is the generic base. Feature-specific modules (ANAF, fiscal printer,
    Zebra labels, DUKIntegrator) add their own job types and result handling
    on top of :class:`DeltatechTcJob`.
    """

    _name = "deltatech.tc.station"
    _description = "Terrabit Connect Station"
    _order = "name"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    api_key = fields.Char(
        string="API Key",
        copy=False,
        readonly=True,
        groups="base.group_system",
        help="Secret used by Terrabit Connect in the X-Station-Key header. Regenerate as needed.",
    )
    active = fields.Boolean(default=True)
    last_seen = fields.Datetime(readonly=True, copy=False)
    tc_version = fields.Char(string="TC Version", readonly=True, copy=False)
    os = fields.Char(string="Operating System", readonly=True, copy=False)
    features = fields.Char(
        readonly=True,
        copy=False,
        help="Comma-separated list of features enabled on the station (reported at heartbeat).",
    )
    note = fields.Text()
    job_ids = fields.One2many("deltatech.tc.job", "station_id")
    job_count = fields.Integer(compute="_compute_job_count")

    # Throttle: don't write last_seen on every poll (30s) — at most once per this interval.
    # Keeps online detection fresh enough while halving DB write churn for many stations.
    _LAST_SEEN_THROTTLE = 60  # seconds

    _api_key_uniq = models.Constraint("unique(api_key)", "The API key must be unique.")

    def _compute_job_count(self):
        data = self.env["deltatech.tc.job"]._read_group([("station_id", "in", self.ids)], ["station_id"], ["__count"])
        mapping = {station.id: count for station, count in data}
        for rec in self:
            rec.job_count = mapping.get(rec.id, 0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("api_key"):
                vals["api_key"] = self._generate_key()
        return super().create(vals_list)

    @api.model
    def _generate_key(self):
        return secrets.token_urlsafe(32)

    def action_regenerate_key(self):
        for rec in self:
            rec.api_key = self._generate_key()
        return True

    @api.model
    def _authenticate(self, api_key):
        """Return the active station for the given key, or an empty recordset."""
        if not api_key:
            return self.browse()
        return self.sudo().search([("api_key", "=", api_key), ("active", "=", True)], limit=1)

    def _touch(self, info=None):
        """Mark the station as "seen now"; optionally store reported metadata.

        ``info`` is the JSON body sent by Terrabit Connect at heartbeat and may
        carry ``version``, ``os`` and ``features`` describing the workstation.
        """
        self.ensure_one()
        info = info or {}
        vals = {}
        if info.get("version") and info["version"] != self.tc_version:
            vals["tc_version"] = info["version"]
        if info.get("os") and info["os"] != self.os:
            vals["os"] = info["os"]
        if info.get("features"):
            features = info["features"]
            if isinstance(features, (list, tuple)):
                features = ",".join(str(f) for f in features)
            if features != self.features:
                vals["features"] = features
        # Throttle last_seen: skip the write if it was refreshed recently and nothing else changed.
        now = fields.Datetime.now()
        if vals or not self.last_seen or (now - self.last_seen).total_seconds() >= self._LAST_SEEN_THROTTLE:
            vals["last_seen"] = now
        if vals:
            self.sudo().write(vals)

    def _notify_manual_heartbeat(self):
        """Send a popup (bus) notification to Terrabit Connect managers on manual heartbeat.

        Only the heartbeat triggered manually from Terrabit Connect; the automatic
        one (every cycle) stays silent.
        """
        self.ensure_one()
        manager_group = self.env.ref("deltatech_tc.group_deltatech_tc_manager", raise_if_not_found=False)
        if not manager_group:
            return
        users = (
            self.env["res.users"]
            .sudo()
            .search([("group_ids", "in", manager_group.id), ("company_ids", "in", self.company_id.id)])
        )
        if not users:
            return
        payload = {
            "type": "success",
            "title": self.env._("Terrabit Connect heartbeat"),
            "message": self.env._("%(name)s sent a manual heartbeat.", name=self.name),
            "sticky": False,
        }
        bus = self.env["bus.bus"].sudo()
        for user in users:
            bus._sendone(user.partner_id, "simple_notification", payload)

    def action_view_jobs(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Terrabit Connect Jobs"),
            "res_model": "deltatech.tc.job",
            "view_mode": "list,form",
            "domain": [("station_id", "=", self.id)],
            "context": {"default_station_id": self.id},
        }

    def action_ping(self):
        """Enqueue a no-op ``ping`` job to verify the station round-trip."""
        self.ensure_one()
        return self.env["deltatech.tc.job"].create(
            {
                "station_id": self.id,
                "company_id": self.company_id.id,
                "job_type": "ping",
            }
        )

    def action_download_config(self):
        """Download a pre-filled ``agent.conf`` (Odoo URL + API key) for this station."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"/tc/config/{self.id}",
            "target": "self",
        }
