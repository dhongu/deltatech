# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from unittest import SkipTest

from odoo import Command
from odoo.modules.registry import Registry
from odoo.tests import tagged
from odoo.tests.common import get_db_name

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestVerifyAccounting(AccountTestInvoicingCommon):
    """MERGE-002 with invoices, sales orders and unreconciled balance: the snapshot of a batch
    keeps the real figures and Verify compares the masters of that batch against them.

    The module depends on `base` only: without `account` and `sale` the test is skipped."""

    @classmethod
    def setUpClass(cls):
        registry = Registry(get_db_name())
        if "account.move" not in registry or "sale.order" not in registry:
            raise SkipTest("account and sale are not installed")
        super().setUpClass()
        cls.env.user.group_ids += cls.env.ref("deltatech_partner_merge.group_partner_merge_apply") | cls.env.ref(
            "sales_team.group_sale_salesman_all_leads"
        )
        Partner = cls.env["res.partner"]
        company = cls.env.company

        def partner(name, vat):
            return Partner.create({"name": name, "vat": vat, "is_company": True, "company_id": company.id})

        cls.a1 = partner("Merge Ledger Alpha SRL", "RO92000001")
        cls.a2 = partner("Merge Ledger Alpha S.R.L.", "RO 92000001")
        cls.b1 = partner("Merge Ledger Beta SRL", "RO92000002")
        cls.b2 = partner("Merge Ledger Beta S.R.L.", "RO92000002")

        cls.invoices = (
            cls.init_invoice("out_invoice", partner=cls.a1, amounts=[100.0], taxes=[], post=True)
            | cls.init_invoice("out_invoice", partner=cls.a1, amounts=[250.0], taxes=[], post=True)
            | cls.init_invoice("out_invoice", partner=cls.a2, amounts=[40.5], taxes=[], post=True)
        )
        cls.orders = cls.env["sale.order"].create(
            [
                {"partner_id": p.id, "order_line": [Command.create({"product_id": cls.product_a.id})]}
                for p in (cls.a1, cls.a2, cls.a2)
            ]
        )
        cls.env.flush_all()

    def _batch(self, name):
        batch = self.env["partner.merge.batch"].create({"name": name, "category_ids": "A,B,C,D", "group_limit": 0})
        batch.action_analyze()
        return batch

    def _apply(self, batch):
        batch.action_simulate()
        batch.action_apply()
        self.assertEqual(batch.state, "done")

    def test_verify_real_figures(self):
        (self.b1 | self.b2).active = False
        self.env.flush_all()
        batch_a = self._batch("MERGE-002 ledger A")
        line = batch_a.line_ids.filtered(lambda line: line.master_id in (self.a1 | self.a2))
        self.assertEqual(len(line), 1)
        self.assertRecordValues(
            line,
            [{"expected_invoices": 3, "expected_sale_orders": 3, "expected_balance": 390.5, "snapshot_taken": True}],
        )
        self._apply(batch_a)
        master = line.master_id
        self.assertFalse(((self.a1 | self.a2) - master).exists())
        self.assertEqual(self.invoices.partner_id, master)
        self.assertEqual(self.orders.partner_id, master)

        # another batch analyzed since: A is still verified against its own figures
        (self.b1 | self.b2).active = True
        self.env.flush_all()
        self._batch("MERGE-002 ledger B")
        batch_a.action_verify()
        self.assertIn("masters checked            : 1", batch_a.report)
        self.assertIn("invoice count mismatches   : 0", batch_a.report)
        self.assertIn("order count mismatches     : 0", batch_a.report)
        self.assertIn("balance mismatches         : 0", batch_a.report)
        self.assertIn("Nothing lost, nothing duplicated.", batch_a.report)

        # a document lost or added on the master is reported
        self.init_invoice("out_invoice", partner=master, amounts=[10.0], taxes=[], post=True)
        self.orders[0].partner_id = self.partner_a
        self.env.flush_all()
        batch_a.action_verify()
        self.assertIn("invoice count mismatches   : 1", batch_a.report)
        self.assertIn("order count mismatches     : 1", batch_a.report)
        self.assertIn("balance mismatches         : 1", batch_a.report)
        self.assertIn("MISMATCHES FOUND", batch_a.report)
