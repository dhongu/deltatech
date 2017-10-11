# coding=utf-8


from odoo import models, fields, api, _

class MrpBom(models.Model):
    _inherit = 'mrp.bom'


    length = fields.Float(related="product_tmpl_id.length")  # x
    width = fields.Float(related="product_tmpl_id.width")   # y
    height = fields.Float(related="product_tmpl_id.height")  # z


    @api.multi
    def action_create_surface_uom(self):
        uom_square_meter = self.env.ref('product.product_uom_square_meter')

        for bom in self:
            dimension = "%s x %s" % (bom.length.is_integer() and int(bom.length) or bom.length,
                                     bom.width.is_integer() and int(bom.width) or bom.width )
            uom = self.env['product.uom'].search([('name', '=', dimension),
                                                  ('category_id', '=', uom_square_meter.category_id.id)], limit=1)
            if not uom:
                bom.product_tmpl_id.onchange_calculate_volume()
                factor = bom.product_tmpl_id.surface
                uom = self.env['product.uom'].create({'name': dimension,
                                                      'category_id': uom_square_meter.category_id.id,
                                                      'uom_type': 'smaller',
                                                      'factor': factor})
