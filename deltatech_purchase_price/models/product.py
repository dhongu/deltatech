# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = "product.product"



class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"



    @api.multi
    def update_standard_price(self):
        for item in self:
            if item.product_tmpl_id.qty_available == 0:
                price = item.product_uom._compute_price(item.price,item.product_tmpl_id.uom_id )
                item.product_tmpl_id.write({'standard_price': price})


    @api.model
    def create(self, vals):
        supplierinfo = super(SupplierInfo, self).create(vals)
        supplierinfo.update_standard_price()
        return supplierinfo

    @api.multi
    def write(self, values):
        res = super(SupplierInfo, self).write(values)
        self.update_standard_price()
        return res

