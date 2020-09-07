# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, models, fields


class res_company(models.Model):
    _inherit = 'res.company'

    warehouse_id = fields.Many2one('stock.warehouse', string="Default Warehouse")
    supplier_id = fields.Many2one('res.partner', string='Default Supplier')

    @api.multi
    def set_supplier(self):
        if self.supplier_id:
            products = self.env['product.product'].search([('purchase_ok', '=', True)])
            for product in products:
                product._select_seller(partner_id=self.supplier_id)
