# ©  2008-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    warranty_header = fields.Html(string="Warranty Header")
    warranty_detail = fields.Html(string="Warranty Detail")
