# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _compute_analytic_account_id(self):
        for line in self:
            if line.move_id.team_id and (
                not line.exclude_from_invoice_tab and line.move_id.is_invoice(include_receipts=True)
            ):
                default = self.env["account.analytic.default"].search(
                    [("sale_team", "=", line.move_id.team_id.id)], limit=1
                )
                if default:
                    line.analytic_account_id = default.analytic_id
                else:
                    super(AccountMoveLine, line)._compute_analytic_account_id()

    def _prepare_analytic_line(self):
        result = []
        for move_line in self:
            if not move_line.exclude_from_invoice_tab and move_line.move_id.is_invoice(include_receipts=True):
                if move_line.company_id.split_sale_analytic:
                    default = self.env["account.analytic.default"].search(
                        [
                            ("analytic_id", "=", move_line.analytic_account_id.id),
                            ("is_split_analytic_rule", "=", True),
                            "|",
                            ("sale_team", "=", move_line.move_id.team_id.id),
                            ("sale_team", "=", False),
                        ]
                    )
                    if default:
                        result += move_line.split_analytic_by_stock(
                            default.stock_analytic_id, default.margin_analytic_id
                        )
                    else:
                        values = super(AccountMoveLine, move_line)._prepare_analytic_line()
                        result += values
        return result

    def split_analytic_by_stock(self, stock_analytic_account, margin_analytic_account):
        """
        Splits analytic line by stock value and margin, on the accounts provided
        :param stock_analytic_account: analytic account for stock value
        :param margin_analytic_account: analytic account for margin value
        :return: array of values (two usual)
        """
        split_result = []
        self.ensure_one()
        # amount = (self.credit or 0.0) - (self.debit or 0.0)
        default_name = self.name or (self.ref or "/" + " -- " + (self.partner_id and self.partner_id.name or "/"))
        if self.move_id.is_sale_document():
            category = "invoice"
            stock_name = default_name + " --stock"
            if self.product_id and self.product_id.detailed_type == "product":
                amount = self.purchase_price
            else:
                amount = 0.0
            split_result.append(
                {
                    "name": stock_name,
                    "date": self.date,
                    "account_id": stock_analytic_account.id,
                    "group_id": stock_analytic_account.group_id.id,
                    "tag_ids": [(6, 0, self._get_analytic_tag_ids())],
                    "unit_amount": self.quantity,
                    "product_id": self.product_id and self.product_id.id or False,
                    "product_uom_id": self.product_uom_id and self.product_uom_id.id or False,
                    "amount": amount,
                    "general_account_id": self.account_id.id,
                    "ref": self.ref,
                    "move_id": self.id,
                    "user_id": self.move_id.invoice_user_id.id or self._uid,
                    "partner_id": self.partner_id.id,
                    "company_id": self.analytic_account_id.company_id.id or self.move_id.company_id.id,
                    "category": category,
                }
            )
            margin_name = default_name + " --margin"
            if self.product_id and self.product_id.detailed_type == "product":
                amount = ((self.credit or 0.0) - (self.debit or 0.0)) - self.purchase_price
            else:
                amount = (self.credit or 0.0) - (self.debit or 0.0)
            split_result.append(
                {
                    "name": margin_name,
                    "date": self.date,
                    "account_id": margin_analytic_account.id,
                    "group_id": margin_analytic_account.group_id.id,
                    "tag_ids": [(6, 0, self._get_analytic_tag_ids())],
                    "unit_amount": self.quantity,
                    "product_id": self.product_id and self.product_id.id or False,
                    "product_uom_id": self.product_uom_id and self.product_uom_id.id or False,
                    "amount": amount,
                    "general_account_id": self.account_id.id,
                    "ref": self.ref,
                    "move_id": self.id,
                    "user_id": self.move_id.invoice_user_id.id or self._uid,
                    "partner_id": self.partner_id.id,
                    "company_id": self.analytic_account_id.company_id.id or self.move_id.company_id.id,
                    "category": category,
                }
            )
        return split_result
