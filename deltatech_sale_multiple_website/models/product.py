# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    check_min_website = fields.Boolean(
        string="Website Check Qty", default=True, help="Check minim & multiple quantity only for website"
    )
