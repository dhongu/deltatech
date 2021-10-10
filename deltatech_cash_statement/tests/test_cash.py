# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestCash(TransactionCase):
    def setUp(self):
        super(TestCash, self).setUp()
        journal_id = self.env["account.journal"].search([("type", "=", "cash")], limit=1)
        self.statement = self.env["account.bank.statement"].create(
            {
                "journal_id": journal_id.id,
            }
        )

    def test_cash_update(self):
        form_cash = Form(self.env["account.cash.update.balances"].with_context(active_ids=self.statement.ids))
        wizard = form_cash.save()
        wizard.do_update_balance()
