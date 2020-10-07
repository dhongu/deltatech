# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    company_standard = fields.Char("Standard of Company", size=64)
    data_sheet = fields.Integer("Data Sheet")
    technical_specification = fields.Integer("Technical Specification")
    standards = fields.Text("Standards")
