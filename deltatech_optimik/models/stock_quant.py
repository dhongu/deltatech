# coding=utf-8


from odoo import api, models, fields



class Quant(models.Model):
    _inherit = 'stock.quant'

    qty_uom = fields.Float('Quantity (in UoM)')
    uom_id = fields.Many2one('product.uom', 'Unit of Measure' )

