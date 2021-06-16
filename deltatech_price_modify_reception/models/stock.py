from odoo import fields, models


class Test(models.Model):
    _inherit = "stock.move"
    _description = "Modify the price list of products at the reception"

    price_list = fields.Float(string="List price", related="product_id.lst_price", readonly=False)
