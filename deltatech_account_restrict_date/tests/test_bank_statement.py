# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestBankStatement(TransactionCase):
    def test_undo_reconciliation(self):
        self.env["account.bank.statement.line"].action_undo_reconciliation()
