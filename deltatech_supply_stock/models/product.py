# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models, registry
from odoo.tools import float_is_zero


class ProductTemplate(models.Model):
    _inherit = "product.template"

    scrap = fields.Float(string="Scrap", help="A factor of 0.1 means a loss of 10% during the consumption.")


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.multi
    def _select_seller(self, partner_id=False, quantity=0.0, date=None, uom_id=False):
        res = super(ProductProduct, self)._select_seller(partner_id, quantity, date, uom_id)
        if not res:
            res = super(ProductProduct, self)._select_seller(partner_id, 0, date, uom_id)
        if not res and not partner_id:
            if self.seller_ids:
                res = self.seller_ids[0]
        return res
