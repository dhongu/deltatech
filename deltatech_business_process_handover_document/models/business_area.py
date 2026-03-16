from odoo import fields, models


class BusinessArea(models.Model):
    _inherit = "business.area"

    handover_checked = fields.Boolean(string="Handover Checked")
