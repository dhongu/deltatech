# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    standard_price = fields.Float(
        company_dependent=False,
        compute="_compute_standard_price",
        inverse="_inverse_standard_price",
        search="_search_standard_price",
    )

    @api.depends_context("valuation_area")
    @api.depends("company_id")
    def _compute_standard_price(self):
        # valuation_area = self.env.context.get("valuation_area", False)

        self._fields["standard_price"]._compute_company_dependent(self)

    def _inverse_standard_price(self):
        self._fields["standard_price"]._inverse_company_dependent(self)

    def _search_standard_price(self, operator, value):
        return self._fields["standard_price"]._search_company_dependent(self, operator, value)
