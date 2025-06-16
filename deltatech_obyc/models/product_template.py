# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    valuation_class_id = fields.Many2one(
        "product.valuation.class",
        string="Valuation Class",
        company_dependent=True,
    )

    def get_product_accounts(self, fiscal_pos=None):
        res = super().get_product_accounts(fiscal_pos)
        if self.valuation_class_id:
            for key in res:
                res[key] = False
            transaction_key = self.env.context.get("transaction_key")
            if not self.env.context.get("transaction_key"):
                raise UserError(_("Transaction key is not defined. Please set it in the context."))
            if transaction_key == "skip":
                return res
            if self.env.context.get("transaction_key"):
                transaction_key = self.env.context.get("transaction_key")
                account_modifier = self.env.context.get("account_modifier")
                valuation_area = self.env.context.get("valuation_area")

                _get_rule_account = self.env["product.account.determination"]._get_rule_account
                rule = _get_rule_account(
                    valuation_area=valuation_area,
                    valuation_class=self.valuation_class_id,
                    transaction_key=transaction_key,
                    account_modifier=account_modifier,
                    company=self.env.company,
                )
                if rule:
                    res["stock_valuation"] = rule.acc_valuation_id.id
                    res["income"] = rule.acc_src_id.id
                    res["expense"] = rule.acc_dest_id.id
                    res["stock_input"] = rule.acc_src_id.id
                    res["stock_output"] = rule.acc_dest_id.id
                else:
                    raise UserError(_("No account found for the given valuation class and transaction key."))

        return res
