from odoo import fields, models


class Raport(models.Model):
    _inherit = "product.template"
    _description = "Raport Packaging"

    plastic = fields.Integer(string="Plastic", readonly=False, default=0)
    wood = fields.Integer(string="Wood", readonly=False, default=0)
    paper = fields.Integer(string="Paper", readonly=False, default=0)
