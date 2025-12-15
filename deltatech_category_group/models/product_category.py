# ©  2008-now Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    category_group_type = fields.Many2one("category.group.type", string="Category type")
    category_group_class = fields.Many2one("category.group.class", string="Category class")
