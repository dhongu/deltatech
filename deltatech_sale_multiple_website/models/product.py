from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    check_min_website = fields.Boolean(
        string="Website Check Quantity",
        default=True,
        help="Apply minimum and multiple quantity rules only on the website.",
    )
