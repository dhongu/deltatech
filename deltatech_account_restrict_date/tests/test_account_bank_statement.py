from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestAccountBankStatement(TransactionCase):

    # se definesc 2 partenerii
    # pentru acesit parteneri se va adauga cate o nota confabila
    # se va indroduce un extras bancar pentru acesti partneri
    # se va face reconcilierea

    def setUp(self):
        super(TestAccountBankStatement, self).setUp()
        # se definesc 2 parteneri
        self.partner1 = self.env["res.partner"].create({"name": "Partner 1"})
        self.partner2 = self.env["res.partner"].create({"name": "Partner 2"})
        # pentru acesit parteneri se va adauga cate o nota contabila
        self.account_move1 = self.env["account.move"].create(
            {
                "partner_id": self.partner1.id,
                "journal_id": self.env["account.journal"].search([("type", "=", "sale")], limit=1).id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "line1",
                            "debit": 100.0,
                            "account_id": self.env["account.account"]
                            .search(
                                [("user_type_id", "=", self.env.ref("account.data_account_type_receivable").id)],
                                limit=1,
                            )
                            .id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "line2",
                            "credit": 100.0,
                            "account_id": self.env["account.account"]
                            .search(
                                [("user_type_id", "=", self.env.ref("account.data_account_type_revenue").id)], limit=1
                            )
                            .id,
                        },
                    ),
                ],
            }
        )
        self.account_move1.post()
        self.account_move2 = self.env["account.move"].create(
            {
                "partner_id": self.partner2.id,
                "journal_id": self.env["account.journal"].search([("type", "=", "sale")], limit=1).id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "line1",
                            "debit": 100.0,
                            "account_id": self.env["account.account"]
                            .search(
                                [("user_type_id", "=", self.env.ref("account.data_account_type_receivable").id)],
                                limit=1,
                            )
                            .id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "line2",
                            "credit": 100.0,
                            "account_id": self.env["account.account"]
                            .search(
                                [("user_type_id", "=", self.env.ref("account.data_account_type_revenue").id)], limit=1
                            )
                            .id,
                        },
                    ),
                ],
            }
        )
        self.account_move2.post()

        # se va adauga un extras bancar pentru acesti partneri
        self.account_bank_statement = self.env["account.bank.statement"].create(
            {
                "journal_id": self.env["account.journal"].search([("type", "=", "bank")], limit=1).id,
                "line_ids": [
                    (0, 0, {"partner_id": self.partner1.id, "amount": 100.0, "name": "line1"}),
                    (0, 0, {"partner_id": self.partner2.id, "amount": 100.0, "name": "line2"}),
                ],
            }
        )

        # se posteaza extrasul bancar
        self.account_bank_statement.post()

        # se va face reconcilierea
        self.account_bank_statement.reconcile()

    def test_account_bank_statement(self):
        self.assertEqual(self.account_bank_statement.state, "confirm")
        with self.assertRaises(UserError):
            self.account_bank_statement.button_undo_reconciliation()
