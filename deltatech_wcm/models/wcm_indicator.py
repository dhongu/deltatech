# © 2026 Terrabit Solutions
# See README.rst file on addons root folder for license details

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .wcm_pillar import WCM_STATES

# Source of the value. "manual" is typed by the user; the others are read from Odoo.
WCM_SOURCES = [
    ("oee", "OEE availability (mrp, last month)"),
    ("mtbf", "MTBF (maintenance, days)"),
    ("mttr", "MTTR (maintenance, days)"),
    ("control_fail", "Quality control failure rate (%)"),
    ("scrap", "Scrap rate (%)"),
    ("on_time", "On-time deliveries (%)"),
    ("manual", "Manual entry"),
]

# Default direction for each source. "manual" keeps what the user chose.
WCM_DIRECTIONS = {
    "oee": "higher",
    "mtbf": "higher",
    "on_time": "higher",
    "mttr": "lower",
    "control_fail": "lower",
    "scrap": "lower",
}


class WcmIndicator(models.Model):
    _name = "wcm.indicator"
    _description = "WCM Indicator"
    _order = "pillar_id, sequence, id"

    name = fields.Char(required=True, translate=True)
    pillar_id = fields.Many2one("wcm.pillar", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    source = fields.Selection(WCM_SOURCES, required=True, default="manual")
    direction = fields.Selection(
        [("higher", "Higher is better"), ("lower", "Lower is better")],
        required=True,
        compute="_compute_direction",
        store=True,
        precompute=True,
        readonly=False,
    )
    unit = fields.Char(default="%")
    period_days = fields.Integer(default=30, help="Length of the period for live sources, counted back from today.")
    target = fields.Float(required=True, digits=(16, 2))
    warning = fields.Float(
        required=True,
        digits=(16, 2),
        help="Threshold between yellow and red. Higher: at or above it is yellow. Lower: at or below it is yellow.",
    )
    manual_value = fields.Float(digits=(16, 2))
    manual_date = fields.Date(help="Date of the manual value. Without it, the indicator has no data.")
    value = fields.Float(compute="_compute_value", digits=(16, 2))
    has_data = fields.Boolean(compute="_compute_value")
    state = fields.Selection(WCM_STATES, compute="_compute_state", search="_search_state")

    @api.depends("source")
    def _compute_direction(self):
        for indicator in self:
            if indicator.source in WCM_DIRECTIONS:
                indicator.direction = WCM_DIRECTIONS[indicator.source]
            elif not indicator.direction:
                indicator.direction = "higher"

    @api.depends("source", "company_id", "period_days", "manual_value", "manual_date")
    def _compute_value(self):
        for indicator in self:
            raw = indicator._get_value()
            indicator.has_data = raw is not None
            indicator.value = raw or 0.0

    @api.depends("has_data", "value", "direction", "target", "warning")
    def _compute_state(self):
        for indicator in self:
            if not indicator.has_data:
                indicator.state = "none"
            elif indicator.direction == "higher":
                if indicator.value >= indicator.target:
                    indicator.state = "green"
                elif indicator.value >= indicator.warning:
                    indicator.state = "yellow"
                else:
                    indicator.state = "red"
            else:
                if indicator.value <= indicator.target:
                    indicator.state = "green"
                elif indicator.value <= indicator.warning:
                    indicator.state = "yellow"
                else:
                    indicator.state = "red"

    def _search_state(self, operator, value):
        # The state depends on live data, so it is evaluated in Python; the table stays small.
        if operator not in ("=", "!=", "in", "not in"):
            return NotImplemented
        states = {value} if isinstance(value, str) else set(value or [])
        matching = self.search([("company_id", "in", self.env.companies.ids)]).filtered(
            lambda indicator: indicator.state in states
        )
        positive = operator in ("=", "in")
        return [("id", "in" if positive else "not in", matching.ids)]

    @api.constrains("direction", "target", "warning")
    def _check_warning_consistency(self):
        for indicator in self:
            if indicator.direction == "higher" and indicator.warning > indicator.target:
                raise ValidationError(
                    self.env._(
                        "“%s”: for an indicator where higher is better, the warning cannot be above the target.",
                        indicator.name,
                    )
                )
            if indicator.direction == "lower" and indicator.warning < indicator.target:
                raise ValidationError(
                    self.env._(
                        "“%s”: for an indicator where lower is better, the warning cannot be below the target.",
                        indicator.name,
                    )
                )

    def _get_value(self):
        """Return the current value as a float, or None when there is no data."""
        self.ensure_one()
        if self.source == "manual":
            return self.manual_value if self.manual_date else None
        method = getattr(self, f"_get_value_{self.source}", None)
        return method() if method else None

    def _get_date_from(self):
        self.ensure_one()
        return fields.Datetime.now() - relativedelta(days=self.period_days or 30)

    def _get_value_oee(self):
        # Odoo computes mrp.workcenter.oee over the last month from productivity logs.
        workcenters = self.env["mrp.workcenter"].search([("company_id", "=", self.company_id.id)])
        values = [oee for oee in workcenters.mapped("oee") if oee]
        return round(sum(values) / len(values), 2) if values else None

    def _get_value_mtbf(self):
        equipments = self.env["maintenance.equipment"].search([("company_id", "=", self.company_id.id)])
        values = [mtbf for mtbf in equipments.mapped("mtbf") if mtbf]
        return round(sum(values) / len(values), 2) if values else None

    def _get_value_mttr(self):
        equipments = self.env["maintenance.equipment"].search([("company_id", "=", self.company_id.id)])
        values = [mttr for mttr in equipments.mapped("mttr") if mttr]
        return round(sum(values) / len(values), 2) if values else None

    def _get_value_control_fail(self):
        domain = [
            ("company_id", "=", self.company_id.id),
            ("quality_state", "in", ["pass", "fail"]),
            ("control_date", ">=", self._get_date_from()),
        ]
        checks = self.env["quality.check"].search(domain)
        if not checks:
            return None
        failed = len(checks.filtered(lambda check: check.quality_state == "fail"))
        return round(failed * 100.0 / len(checks), 2)

    def _get_value_scrap(self):
        date_from = self._get_date_from()
        scrap_moves = self.env["stock.move"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("is_scrap", "=", True),
                ("state", "=", "done"),
                ("date", ">=", date_from),
            ]
        )
        productions = self.env["mrp.production"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("state", "=", "done"),
                ("date_finished", ">=", date_from),
            ]
        )
        produced = sum(productions.mapped("product_qty"))
        if not produced:
            return None
        return round(sum(scrap_moves.mapped("product_qty")) * 100.0 / produced, 2)

    def _get_value_on_time(self):
        pickings = self.env["stock.picking"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("picking_type_code", "=", "outgoing"),
                ("state", "=", "done"),
                ("date_done", ">=", self._get_date_from()),
            ]
        )
        if not pickings:
            return None
        on_time = len(
            [
                picking
                for picking in pickings
                if not picking.scheduled_date or picking.date_done <= picking.scheduled_date
            ]
        )
        return round(on_time * 100.0 / len(pickings), 2)
