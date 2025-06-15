# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    valuation_area_id = fields.Many2one("valuation.area", string="Valuation Area")

    def _get_account_modifier(self):
        account_modifier = self.env["account.modifier"]
        return account_modifier

    def _compute_account_id(self):
        res = super()._compute_account_id()

        product_lines = self.filtered(lambda line: line.display_type == "product" and line.move_id.is_invoice(True))
        for line in product_lines:
            if not line.product_id.valuation_class_id:
                continue

            valuation_area = self.valuation_area_id
            if not valuation_area:
                valuation_area = self.company_id.valuation_area_id

                stock_move = line.move_id.stock_move_id
                if "purchase_line_id" in line._fields:
                    if line.purchase_line_id:
                        stock_move = next(iter(line.purchase_line_id.move_ids), None)
                if "sale_line_ids" in line._fields:
                    if line.sale_line_ids:
                        stock_move = next(iter(line.sale_line_ids.mapped("move_ids")), None)
                if stock_move:
                    valuation_area = stock_move._get_valuation_area()

            if not valuation_area:
                raise UserError("Valuation area is not defined")

            transaction_key = False

            if line.move_id.is_sale_document(include_receipts=True):
                transaction_key = "stock_income"
            elif line.move_id.is_purchase_document(include_receipts=True):
                transaction_key = "stock_receipt"

            account_modifier = self._get_account_modifier()

            _get_rule_account = self.env["product.account.determination"]._get_rule_account
            rule = _get_rule_account(
                valuation_area=valuation_area,
                valuation_class=self.product_id.valuation_class_id,
                transaction_key=transaction_key,
                account_modifier=account_modifier,
                company=self.company_id,
            )

            line.account_id = rule.acc_dest_id
            line.valuation_area_id = valuation_area

        return res
