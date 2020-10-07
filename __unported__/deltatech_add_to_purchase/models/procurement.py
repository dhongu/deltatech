# -*- coding: utf-8 -*-

from openerp import models, fields, api, _


class procurement_order(models.Model):
    _inherit = "procurement.order"

    supplier_id = fields.Many2one('res.partner', string='Supplier')

    @api.model
    def _get_product_supplier(self, procurement):
        if 'supplier_id' in self.env.context:
            procurement.write({'supplier_id': self.env.context['supplier_id']})
        if procurement.supplier_id:
            return procurement.supplier_id
        else:
            return super(procurement_order, self)._get_product_supplier(procurement)
