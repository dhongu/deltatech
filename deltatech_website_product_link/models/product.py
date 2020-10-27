# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    alternative_link = fields.Char()
