# ©  2023-now Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    category_group_type = fields.Many2one(
        "category.group.type", related="product_id.categ_id.category_group_type", store=True, readonly=True, index=True
    )
    category_group_class = fields.Many2one(
        "category.group.class",
        related="product_id.categ_id.category_group_class",
        store=True,
        readonly=True,
        index=True,
    )
