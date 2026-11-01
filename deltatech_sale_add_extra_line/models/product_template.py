# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    extra_product_id = fields.Many2one(
        "product.product", help="Product added automatically as an extra line when this product is ordered"
    )
    extra_percent = fields.Float(
        help="Percent of the main line price used as the price of the extra line. If zero, the extra "
        "line keeps the standard price computed for its own product (price list or vendor price, "
        "currency and unit of measure of the order)"
    )
    extra_qty = fields.Float(
        default=1.0,
        help="Multiplier for the quantity of the extra line: extra quantity = quantity of the main line x this value",
    )
