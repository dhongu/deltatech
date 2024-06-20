# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    extra_product_id = fields.Many2one("product.product")
    extra_percent = fields.Float()
    extra_qty = fields.Float(default=1.0)
