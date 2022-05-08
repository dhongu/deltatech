# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company, required=True)
