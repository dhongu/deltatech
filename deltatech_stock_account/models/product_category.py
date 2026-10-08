# ©  2008-2018 Fekete Mihai <mihai.fekete@forbiom.eu>
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    # Accounting settings copied from a category to its descendants and from the parent on onchange
    _propagated_account_fields = (
        "property_price_difference_account_id",
        "property_account_expense_categ_id",
        "property_account_income_categ_id",
        "property_stock_valuation_account_id",
        "property_stock_journal",
        "property_cost_method",
        "property_valuation",
    )

    def write(self, vals):
        res = super().write(vals)
        if "property_stock_valuation_account_id" in vals:
            self.propagate_account()
        return res

    def _get_propagated_account_values(self):
        self.ensure_one()
        return {
            field_name: self._fields[field_name].convert_to_write(self[field_name], self)
            for field_name in self._propagated_account_fields
        }

    def propagate_account(self):
        if self.env.context.get("propagate_account"):
            return
        for categ in self:
            if not categ.property_stock_valuation_account_id:
                continue
            children = self.search([("id", "child_of", categ.ids), ("id", "!=", categ.id)])
            if not children:
                continue
            children.with_context(propagate_account=True).write(categ._get_propagated_account_values())

    @api.onchange("parent_id")
    def _onchange_parent_id(self):
        if self.parent_id:
            for field_name in self._propagated_account_fields:
                self[field_name] = self.parent_id[field_name]
