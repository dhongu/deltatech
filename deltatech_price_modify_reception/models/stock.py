from odoo import fields, models


class Test(models.Model):
    _inherit = "stock.move"
    _description = "Modify the price list of products at the reception"

    price_list = fields.Float(string="Price List", related="product_tmpl_id.list_price", readonly=False, store=False)
    picking_type = fields.Selection(related="picking_type_id.code")
