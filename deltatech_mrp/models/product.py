# ©  2008-2019 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"
    cost_categ = fields.Selection(
        [("raw", "Raw materials"), ("semi", "Semi-products"), ("pak", "Packing Material")], string="Cost Category"
    )
