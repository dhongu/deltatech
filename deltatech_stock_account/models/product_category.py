# ©  2008-2018 Fekete Mihai <mihai.fekete@forbiom.eu>
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    def write(self, vals):
        res = super().write(vals)
        if "property_stock_valuation_account_id" in vals:
            self.propagate_account()
        return res

    def propagate_account(self):
        if self.env.context.get("propagate_account"):
            return
        for categ in self:
            if not categ.property_stock_valuation_account_id:
                continue
            children = self.search([("id", "child_of", [categ.id])])
            if not children:
                continue
            values = {
                # Cont diferență de preț
                "property_account_creditor_price_difference_categ": categ.property_account_creditor_price_difference_categ.id,
                # Cont de cheltuieli
                "property_account_expense_categ_id": categ.property_account_expense_categ_id.id,
                # Cont de venituri
                "property_account_income_categ_id": categ.property_account_income_categ_id.id,
                #  Cont Intrare Stoc
                "property_stock_account_input_categ_id": categ.property_stock_account_input_categ_id.id,
                # Cont ieșire din stoc
                "property_stock_account_output_categ_id": categ.property_stock_account_output_categ_id.id,
                # Cont Evaluare  Stoc
                "property_stock_valuation_account_id": categ.property_stock_valuation_account_id.id,
                # Jurnal de stoc
                "property_stock_journal": categ.property_stock_journal.id,
                # Metodă de cost
                "property_cost_method": categ.property_cost_method,
                # property_valuation
                "property_valuation": categ.property_valuation,
            }
            children.with_context(propagate_account=True).write(values)

    @api.onchange("parent_id")
    def _onchange_parent_id(self):
        if self.parent_id:
            self.property_stock_valuation_account_id = self.parent_id.property_stock_valuation_account_id
            self.property_account_expense_categ_id = self.parent_id.property_account_expense_categ_id
            self.property_account_income_categ_id = self.parent_id.property_account_income_categ_id
            self.property_stock_account_input_categ_id = self.parent_id.property_stock_account_input_categ_id
            self.property_stock_account_output_categ_id = self.parent_id.property_stock_account_output_categ_id
            self.property_account_creditor_price_difference_categ = (
                self.parent_id.property_account_creditor_price_difference_categ
            )
            self.property_stock_journal = self.parent_id.property_stock_journal
            self.property_cost_method = self.parent_id.property_cost_method
            self.property_valuation = self.parent_id.property_valuation
