# ©  2015-2017 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models, tools
from odoo.exceptions import RedirectWarning, ValidationError, except_orm

from odoo.addons import decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = "product.template"

    cost_price = fields.Monetary("Cost price", compute="_compute_cost_price")

    @api.multi
    def _compute_cost_price(self):
        for template in self:
            amount = 0.0
            for variant in template.product_variant_ids:
                amount += variant.standard_price
            if template.product_variant_count > 0:
                template.cost_price = amount / template.product_variant_count
