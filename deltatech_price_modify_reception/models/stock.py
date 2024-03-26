from odoo import fields, models


class Picking(models.Model):
    _inherit = "stock.picking"

    can_modify_price_list_at_reception = fields.Boolean(related="company_id.can_modify_price_list_at_reception")


class StockMove(models.Model):
    _inherit = "stock.move"

    price_list = fields.Float(string="Price List", related="product_tmpl_id.list_price", readonly=False, store=False)
