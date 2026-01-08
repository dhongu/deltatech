# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    extra_product_id = fields.Many2one("product.product", help="Product sold as extra")
    extra_percent = fields.Float(
        help="Percent used to calculate extra product price. If zero, extra product price will be used directly"
    )
    extra_qty = fields.Float(default=1.0, help="Quantity sold as extra")
