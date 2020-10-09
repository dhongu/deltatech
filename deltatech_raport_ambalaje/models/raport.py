from odoo import fields, models


class Raport(models.Model):
    _inherit = "product.product"
    _description = "Raport ambalaje"

    plastic = fields.Integer(string="Plastic", readonly=False)
    lemn = fields.Integer(string="Wood", readonly=False, default=0)
    hartie = fields.Integer(string="hartie", default=0)
