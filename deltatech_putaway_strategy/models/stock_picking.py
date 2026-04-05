from odoo import fields, models


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    avoid_putaway_rules = fields.Boolean(string="Avoid Putaway Rules")
