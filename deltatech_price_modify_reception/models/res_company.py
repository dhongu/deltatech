from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    can_modify_price_list_at_reception = fields.Boolean()
