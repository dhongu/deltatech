# ©  2008-2023 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def create_payment_from_statement(self):
        for move in self:
            if move.move_type != "entry":
                continue
            domain = [("move_id", "=", move.id)]
            payment = self.env["account.payment"].search(domain)
            if payment:
                continue
            statement_line = self.env["account.bank.statement.line"].search(domain)
            if not statement_line:
                continue

            values = {
                "move_id": move.id,
                "partner_id": statement_line.partner_id.id,
                "line_ids": [],
                "amount": statement_line.amount,
                "payment_type": "inbound" if statement_line.amount > 0 else "outbound",
            }

            self.env["account.payment"].create(values)
