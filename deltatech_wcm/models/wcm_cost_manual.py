# © 2026 Terrabit Solutions
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class WcmCostManual(models.Model):
    _name = "wcm.cost.manual"
    _description = "WCM Manual Cost (energy, waste)"
    _order = "date_from desc, id desc"
    _check_company_auto = True

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, index=True)
    currency_id = fields.Many2one(related="company_id.currency_id")
    workcenter_id = fields.Many2one("mrp.workcenter", required=True, check_company=True, index=True)
    cost_type = fields.Selection([("energy", "Energy"), ("waste", "Waste")], required=True, default="energy")
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    amount = fields.Monetary(required=True, currency_field="currency_id")

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for cost in self:
            if cost.date_to < cost.date_from:
                raise ValidationError(self.env._("“%s”: the end date cannot be before the start date.", cost.name))

    def _get_amount_for_period(self, date_from, date_to):
        """Amount prorated to the days of [date_from, date_to] (dates) covered by this cost."""
        self.ensure_one()
        start = max(self.date_from, date_from)
        end = min(self.date_to, date_to)
        if end < start:
            return 0.0
        total_days = (self.date_to - self.date_from).days + 1
        return self.amount * ((end - start).days + 1) / total_days
