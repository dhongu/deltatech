from odoo import fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    discount_policy = fields.Selection(
        selection=[
            ("with_discount", "Discount included in the price"),
            ("without_discount", "Show public price & discount to the customer"),
        ],
        string="Discount Policy",
        default="with_discount",
        required=True,
    )
