# coding=utf-8


from odoo import models, fields, api, _

class MrpBom(models.Model):
    _inherit = 'mrp.bom'


    length = fields.Float(related="product_tmpl_id.length")  # x
    width = fields.Float(related="product_tmpl_id.width")   # y
    height = fields.Float(related="product_tmpl_id.height")  # z


    @api.multi
    def action_create_surface_uom(self):
         for bom in self:
            self.env['uom.uom'].search_surface(bom.length,  bom.width)
