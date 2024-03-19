# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _prepare_analytic_line(self):
        result = []
        for move_line in self:
            if not move_line.company_id.split_sale_analytic or move_line.move_id.move_type not in [
                "out_invoice",
                "out_refund",
            ]:
                return super()._prepare_analytic_line()
            if move_line.move_id.team_id:
                default = self.env["account.analytic.default"].search(
                    [("sale_team", "=", move_line.move_id.team_id.id)], limit=1
                )
            else:
                default = self.env["account.analytic.default"].account_get(
                    product_id=move_line.product_id.id,
                    partner_id=move_line.partner_id.commercial_partner_id.id
                    or move_line.move_id.partner_id.commercial_partner_id.id,
                    account_id=move_line.account_id.id,
                    user_id=move_line.env.uid,
                    date=move_line.date,
                    company_id=move_line.move_id.company_id.id,
                )
            if default.is_split_analytic_rule:
                result.append(self.split_analytic_by_stock(default.stock_analytic_id, default.margin_analytic_id)[0])
                result.append(self.split_analytic_by_stock(default.stock_analytic_id, default.margin_analytic_id)[1])
            else:
                result.append(move_line._prepare_analytic_line())
        return result

    def split_analytic_by_stock(self, stock_analytic_account, margin_analytic_account):
        split_result = []
        self.ensure_one()
        # amount = (self.credit or 0.0) - (self.debit or 0.0)
        default_name = self.name or (self.ref or "/" + " -- " + (self.partner_id and self.partner_id.name or "/"))
        if self.move_id.is_sale_document():
            category = "invoice"
            stock_name = default_name + " --stock"
            amount = self.purchase_price
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
            amount = ((self.credit or 0.0) - (self.debit or 0.0)) - self.purchase_price
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
