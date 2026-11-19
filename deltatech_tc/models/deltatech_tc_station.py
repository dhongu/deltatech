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
    fiscal_driver = fields.Char(
        readonly=True,
        copy=False,
        help="Cash register driver configured on the station (reported at heartbeat): fiscalwire, simulated...",
    )
    simulated_devices = fields.Char(
        readonly=True,
        copy=False,
        help="Devices simulated by Terrabit Connect on this station (reported at heartbeat): "
        "the cash register (fiscal) and the card terminals (terminal:<id>). Their receipts and "
        "card payments are not real.",
    )
    is_simulated = fields.Boolean(
        string="Simulation",
        readonly=True,
        copy=False,
        help="At least one device of the station is simulated.",
    )
    agent_name = fields.Char(
        string="Agent",
        readonly=True,
        copy=False,
        help="Program running on the station, as reported at heartbeat (e.g. tc-postgresql). "
        "Empty for the Terrabit Connect desktop app.",
    )
    capabilities = fields.Json(
        readonly=True,
        copy=False,
        help="What the station can run, reported at heartbeat. For Terrabit Connect PostgreSQL: "
        "{profile: [installed queries]}.",
    )
    capabilities_display = fields.Text(string="PostgreSQL queries", compute="_compute_capabilities_display")
    note = fields.Text()
    job_ids = fields.One2many("deltatech.tc.job", "station_id")
    job_count = fields.Integer(compute="_compute_job_count")

    # Throttle: don't write last_seen on every poll (30s) — at most once per this interval.
    # Keeps online detection fresh enough while halving DB write churn for many stations.
    _LAST_SEEN_THROTTLE = 60  # seconds

    _api_key_uniq = models.Constraint("unique(api_key)", "The API key must be unique.")

    @api.depends("capabilities")
    def _compute_capabilities_display(self):
        for rec in self:
            caps = rec.capabilities if isinstance(rec.capabilities, dict) else {}
            rec.capabilities_display = (
                "\n".join(
                    f"{profile}: {', '.join(queries)}" if queries else profile
                    for profile, queries in sorted(caps.items())
                )
                or False
            )

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
        carry ``version``, ``os``, ``features``, ``fiscal_driver`` and ``simulated`` describing the
        workstation. Terrabit Connect PostgreSQL also sends ``agent`` and ``pg_profiles``
        (``{profile: [installed queries]}``), stored in ``capabilities``.
        """
        self.ensure_one()
        info = info or {}
        vals = {}
        if info.get("version") and info["version"] != self.tc_version:
            vals["tc_version"] = info["version"]
        if info.get("os") and info["os"] != self.os:
            vals["os"] = info["os"]
        if info.get("fiscal_driver") and info["fiscal_driver"] != self.fiscal_driver:
            vals["fiscal_driver"] = info["fiscal_driver"]
        if "simulated" in info:
            # Raportat la fiecare heartbeat, și gol: o stație scoasă din simulare se curăță.
            simulated = info.get("simulated") or []
            if isinstance(simulated, (list, tuple)):
                simulated = ",".join(str(d) for d in simulated)
            simulated = str(simulated or "")
            if simulated != (self.simulated_devices or ""):
                vals["simulated_devices"] = simulated or False
                vals["is_simulated"] = bool(simulated)
        if info.get("agent") and info["agent"] != self.agent_name:
            vals["agent_name"] = str(info["agent"])
        if "pg_profiles" in info:
            profiles = info.get("pg_profiles")
            profiles = (
                {
                    str(k): [q for q in v if isinstance(q, str)] if isinstance(v, list) else []
                    for k, v in profiles.items()
                }
                if isinstance(profiles, dict)
                else {}
            )
            if profiles != (self.capabilities or {}):
                vals["capabilities"] = profiles
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

    def features_list(self):
        """The features the station announced, as a list of whole names."""
        self.ensure_one()
        return [f.strip() for f in (self.features or "").split(",") if f.strip()]

    @api.model
    def _tc_find(self, feature, company=None):
        """The first active station of the company that announces ``feature``.

        ``feature`` is compared as a whole element of the list (``pg:erp`` does not
        match ``pg:erp_test``). Feature modules use it to address their jobs, e.g.
        ``_tc_find("pg:erp")`` for the station that reads the ``erp`` database profile.
        """
        company = company or self.env.company
        candidates = self.sudo().search(
            [("company_id", "=", company.id), ("active", "=", True), ("features", "ilike", feature)],
            order="last_seen desc, name, id",
        )
        return candidates.filtered(lambda s: feature in s.features_list())[:1]

    def _tc_has_pg_query(self, profile, query):
        """Did the station announce ``query`` in ``profile`` at its last heartbeat?

        Lets a feature module refuse with a clear message ("query x is not installed on
        station Y") before queueing a job that would only fail on the station.
        """
        self.ensure_one()
        caps = self.capabilities if isinstance(self.capabilities, dict) else {}
        return query in (caps.get(profile) or [])

    def _tc_has_pg_sql(self, profile):
        """Does the station accept SQL sent by Odoo for ``profile`` (``allow_sql`` on the
        station, announced as the feature ``pg_sql:<profile>``)?"""
        self.ensure_one()
        return f"pg_sql:{profile}" in self.features_list()

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
        """Download a pre-filled ``station.conf`` (Odoo URL + API key) for this station."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"/tc/config/{self.id}",
            "target": "self",
        }
