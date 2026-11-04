# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models
from odoo.tools import SQL


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _compute_currency_id(self):
        main_company = self.env["res.company"]._get_main_company()
        for template in self:
            template.currency_id = template.company_id.sudo().price_currency_id.id or main_company.price_currency_id.id

    def _compute_sql_currency_id(self, table):
        # în 20 currency_id are și variantă SQL (căutare/grupare/ordonare): aceeași regulă ca în Python
        main_company = self.env["res.company"]._get_main_company()
        return SQL("COALESCE(%s, %s)", table.company_id.price_currency_id, main_company.price_currency_id.id)
