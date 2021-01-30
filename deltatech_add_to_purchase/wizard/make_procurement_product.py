# -*- coding: utf-8 -*-

from openerp import models, fields, api, _


class make_procurement(models.TransientModel):
    _inherit = 'make.procurement'

    supplier_id = fields.Many2one('res.partner', string='Supplier', domain=[('supplier', '=', True)])

    @api.multi
    def make_procurement(self):
        if self.supplier_id:
            self = self.with_context(supplier_id=self.supplier_id.id)
        res = super(make_procurement, self).make_procurement()

        if self.supplier_id:
            procurement = self.env['procurement.order'].browse(res['res_id'])
            procurement.write({'supplier_id': self.supplier_id.id})

        return res

    @api.model
    def default_get(self, fields):
        res = super(make_procurement, self).default_get(fields)
        if 'product_id' in res:
            product = self.env['product.product'].browse(res['product_id'])
            if product.seller_id:
                res['supplier_id'] = product.seller_id.id
        return res
