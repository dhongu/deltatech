# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models, registry, _
from odoo.tools import float_is_zero


# class SuppliferInfo(models.Model):
#     _inherit = "product.supplierinfo"
#
#
#     def filtered(self, func):
#
#         res = super(SuppliferInfo, self).filtered(func)
#         if not res:
#             if self.env.user.company_id.supplier_id:
#                 res = self.env['product.supplierinfo'].create({'product_id': self.id,
#                                                                'name': self.env.user.company_id.supplier_id.id})
#         return res


class ProductTemplate(models.Model):
    _inherit = "product.template"

    scrap = fields.Float(string="Scrap", help="A factor of 0.1 means a loss of 10% during the consumption.")


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.multi
    def _select_seller(self, partner_id=False, quantity=0.0, date=None, uom_id=False, params=False):

        res = super(ProductProduct, self)._select_seller(partner_id, quantity, date, uom_id, params)

        if not res:
            if self.env.user.company_id.supplier_id and \
                    (not partner_id or partner_id == self.env.user.company_id.supplier_id):
                res = self.env['product.supplierinfo'].create({
                    # 'product_id': self.id,
                    'product_tmpl_id': self.product_tmpl_id.id,
                    'company_id': self.env.user.company_id.id,
                    'name': self.env.user.company_id.supplier_id.id
                })

        return res
