# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license detai

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    stock_valuation = fields.Boolean(string="Stock Valuation")

    def recompute_valuation_amount(self):
        valuations = self.env["product.valuation"]
        for product in self:
            for variant in product.product_variant_ids:
                company = variant.company_id or self.env.company
                account = variant.categ_id.property_stock_valuation_account_id
                if not account:
                    continue

                if not account.stock_valuation:
                    account.stock_valuation = True

                valuation_area = company.valuation_area_id
                valuations |= self.env["product.valuation"].get_valuation(
                    variant.id, valuation_area.id, account.id, company.id
                )

        valuations.recompute_amount()
