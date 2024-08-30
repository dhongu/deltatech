from odoo import fields, models


class BusinessProject(models.Model):
    _inherit = "business.project"

    provider_company = fields.Char(string="Provider Company")
    provider_representative = fields.Many2one(
        "res.partner",
        string="Provider Representative",
        domain="[('is_company', '=', False)]",
    )

    recipient_company = fields.Char(string="Recipient Company")
    recipient_representative = fields.Many2one(
        "res.partner",
        string="Recipient Representative",
        domain="[('is_company', '=', False)]",
    )

    provider_testers = fields.Many2many("res.partner", string="Provider Testers", relation="tester_provider")
    recipient_testers = fields.Many2many("res.partner", string="Recipient Testers", relation="tester_recipient")
