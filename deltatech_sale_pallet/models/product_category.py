# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    pallet = fields.Boolean()
