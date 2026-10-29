# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PurchaseTarget(models.Model):
    _name = "purchase.target"
    _description = "Purchase Target"
    _order = "year desc, manufacturer_id"
    _check_company_auto = True

    name = fields.Char(compute="_compute_name", store=True)
    manufacturer_id = fields.Many2one(
        "res.partner",
        string="Manufacturer",
        required=True,
        index=True,
        check_company=True,
        domain=[("is_manufacturer", "=", True)],
    )
    year = fields.Integer(required=True, default=lambda self: fields.Date.context_today(self).year)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related="company_id.currency_id")
    target_type = fields.Selection(
        [("amount", "Amount"), ("qty", "Quantity")],
        string="Target Type",
        required=True,
        default="amount",
        help="Amount: purchases without VAT, in the company currency. "
        "Quantity: purchased quantities, in the unit of measure of each product.",
    )
    # only the bills of these vendors count; the resellers of the manufacturer are left out
    partner_ids = fields.Many2many(
        "res.partner",
        string="Vendors",
        check_company=True,
        compute="_compute_partner_ids",
        store=True,
        readonly=False,
        help="Vendor bills counted as achieved. By default the manufacturer itself; "
        "add the other companies through which the manufacturer invoices.",
    )
    line_ids = fields.One2many("purchase.target.line", "target_id", string="Targets", copy=True)
    active = fields.Boolean(default=True)
    note = fields.Html()

    _manufacturer_year_uniq = models.Constraint(
        "UNIQUE(manufacturer_id, year, company_id)",
        "There is already a target for this manufacturer and year.",
    )

    @api.constrains("year")
    def _check_year(self):
        for target in self:
            if not 2000 <= target.year <= 2100:
                raise ValidationError(self.env._("The year of a target must be between 2000 and 2100."))

    @api.depends("manufacturer_id", "year")
    def _compute_name(self):
        for target in self:
            target.name = f"{target.manufacturer_id.name or ''} {target.year or ''}".strip()

    @api.depends("manufacturer_id")
    def _compute_partner_ids(self):
        for target in self:
            target.partner_ids = target.manufacturer_id.commercial_partner_id

    def action_view_lines(self):
        action = self.env["ir.actions.act_window"]._for_xml_id("deltatech_purchase_target.action_purchase_target_line")
        action["domain"] = [("target_id", "in", self.ids)]
        action["context"] = {}
        return action
