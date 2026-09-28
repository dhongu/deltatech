# ©  2026 Terrabit
# Based on the MD Trade customer analysis modules, © 2026 MD Trade Concept SRL
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CustomerSegmentConfig(models.Model):
    """Per-company settings of the segmentation engine.

    The thresholds were hard-coded in the MD Trade code, in RON. They live here
    so that every company can tune them to its own order sizes and currency.
    Kept on a dedicated model: no field is added to res.company.
    """

    _name = "deltatech.customer.segment.config"
    _description = "Customer Segment Settings"
    _check_company_auto = True

    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one(related="company_id.currency_id")

    basis = fields.Selection(
        [("invoices", "Posted customer invoices"), ("orders", "Confirmed sales orders")],
        default="invoices",
        required=True,
        help="Posted invoices: untaxed amounts in company currency, credit notes deducted.\n"
        "Confirmed orders: untaxed order amounts converted at the order rate.",
    )
    only_companies = fields.Boolean(
        string="Only companies (B2B)",
        help="Skip individuals. Useful when the retail customers are not followed by the sales team.",
    )

    # Comparison window used for the growth / decline signals
    period_months = fields.Integer(string="Comparison period (months)", default=6, required=True)

    # Buying rhythm
    default_interval_days = fields.Integer(
        string="Default rhythm (days)",
        default=60,
        help="Rhythm assumed for a customer with a single purchase: there is no interval to measure.",
    )
    at_risk_factor = fields.Float(
        default=1.5, help="Silent for more than this many own rhythms: the customer is at risk."
    )
    dormant_factor = fields.Float(default=3.0, help="Silent for more than this many own rhythms: dormant.")
    lost_after_days = fields.Integer(string="Lost after (days)", default=365)
    new_days = fields.Integer(string="New customer window (days)", default=90)
    new_max_count = fields.Integer(string="New customer max. purchases", default=2)

    # Portfolio classification
    inactive_days_1 = fields.Integer(string="Inactive, level 1 (days)", default=60)
    inactive_days_2 = fields.Integer(string="Inactive, level 2 (days)", default=90)
    inactive_days_3 = fields.Integer(string="Inactive, level 3 (days)", default=180)
    overdue_days = fields.Integer(
        string="Overdue risk after (days)", default=30, help="Oldest overdue invoice older than this: payment risk."
    )
    overdue_count = fields.Integer(
        string="Overdue risk from (invoices)", default=3, help="At least this many overdue invoices: payment risk."
    )
    overdue_tolerance = fields.Monetary(
        default=0.5, help="Open balances below this amount are ignored (rounding differences)."
    )
    decline_pct = fields.Integer(
        string="Decline threshold (%)",
        default=70,
        help="Declining: current period sales fall below this share of the previous period.",
    )
    decline_min_previous = fields.Monetary(
        string="Decline min. previous sales",
        default=5000.0,
        help="The decline signal is raised only for customers who bought at least this much in the previous period.",
    )
    growth_pct = fields.Integer(
        string="Growth threshold (%)",
        default=30,
        help="Growing: current sales above the previous period by this share.",
    )
    high_value_min = fields.Monetary(
        string="High value from", default=50000.0, help="Lifetime sales from which a customer is a key account."
    )
    high_potential_min = fields.Monetary(string="High potential from", default=25000.0)
    high_potential_avg = fields.Monetary(string="High potential min. average", default=4000.0)
    small_order_avg = fields.Monetary(
        string="Small orders below", default=3000.0, help="Frequent buyer with an average document below this amount."
    )
    top_share_pct = fields.Integer(string="Top customers (%)", default=20)
    top_min_count = fields.Integer(string="Top customers min. count", default=4)
    neglected_contact_days = fields.Integer(
        string="No recent contact after (days)",
        default=21,
        help="No message logged on the customer for this many days raises the risk score.",
    )

    last_run = fields.Datetime(readonly=True, copy=False)

    _company_uniq = models.Constraint("unique(company_id)", "The segmentation settings already exist for this company.")

    @api.constrains(
        "period_months", "at_risk_factor", "dormant_factor", "inactive_days_1", "inactive_days_2", "inactive_days_3"
    )
    def _check_values(self):
        for config in self:
            if config.period_months < 1:
                raise ValidationError(self.env._("The comparison period must be at least one month."))
            if not 0 < config.at_risk_factor <= config.dormant_factor:
                raise ValidationError(
                    self.env._("The at-risk factor must be positive and not above the dormant factor.")
                )
            if not 0 < config.inactive_days_1 <= config.inactive_days_2 <= config.inactive_days_3:
                raise ValidationError(self.env._("The inactivity levels must be positive and increasing."))

    @api.model
    def _get_for_company(self, company):
        """Settings of a company, created with the defaults on first use."""
        config = self.sudo().search([("company_id", "=", company.id)], limit=1)
        if not config:
            config = self.sudo().create({"company_id": company.id})
        return config

    @api.model
    def action_open_settings(self):
        config = self._get_for_company(self.env.company)
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Customer Segmentation"),
            "res_model": self._name,
            "res_id": config.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_recompute(self):
        self.ensure_one()
        self.env["deltatech.customer.segment"]._recompute_company(self.company_id)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": self.env._("Customer segments recomputed."),
                "next": {"type": "ir.actions.client", "tag": "soft_reload"},
            },
        }
