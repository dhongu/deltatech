# ©  2015-2022 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _make_po_get_domain(self, company_id, values, partner):
        new_values = dict(values)
        new_values["group_id"] = False
        domain = super(StockRule, self)._make_po_get_domain(company_id, new_values, partner)
        return domain
