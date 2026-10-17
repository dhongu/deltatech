# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestVerifyBatch(TransactionCase):
    """MERGE-002: the verification of a batch uses that batch's own snapshot, not the
    working tables left behind by the latest analysis."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({"name": "MERGE-002 company"})
        Partner = cls.env["res.partner"]

        def partner(name, vat):
            return Partner.create({"name": name, "vat": vat, "is_company": True, "company_id": cls.company.id})

        # batch A: one group
        cls.a1 = partner("Merge Verify Alpha SRL", "RO91000001")
        cls.a2 = partner("Merge Verify Alpha S.R.L.", "RO 91000001")
        # batch B: two other groups
        cls.b1 = partner("Merge Verify Beta SRL", "RO91000002")
        cls.b2 = partner("Merge Verify Beta S.R.L.", "RO91000002")
        cls.c1 = partner("Merge Verify Gamma SRL", "RO91000003")
        cls.c2 = partner("Merge Verify Gamma S.R.L.", "RO91000003")

        cls.operator = new_test_user(
            cls.env,
            login="merge002_operator",
            groups="base.group_user,base.group_partner_manager,deltatech_partner_merge.group_partner_merge_apply",
            company_id=cls.company.id,
            company_ids=[Command.set(cls.company.ids)],
        )
        cls.env.flush_all()

    def _batch(self, name):
        batch = self.env(user=self.operator)["partner.merge.batch"].create(
            {"name": name, "category_ids": "A,B", "group_limit": 0}
        )
        batch.action_analyze()
        return batch

    def _apply(self, batch):
        batch.action_simulate()
        batch.action_apply()
        self.assertEqual(batch.state, "done")

    def _hide_b(self):
        # keep B's partners out of batch A: they are created as candidates only for B
        (self.b1 | self.b2 | self.c1 | self.c2).write({"active": False})
        self.env.flush_all()

    def _show_b(self):
        (self.b1 | self.b2 | self.c1 | self.c2).write({"active": True})
        self.env.flush_all()

    def test_verify_older_batch_after_newer_analysis(self):
        self._hide_b()
        batch_a = self._batch("MERGE-002 A")
        self.assertEqual(len(batch_a.line_ids), 1)
        self._apply(batch_a)
        self._show_b()

        batch_b = self._batch("MERGE-002 B")
        self.assertEqual(len(batch_b.line_ids), 2)

        batch_a.action_verify()
        self.assertIn("masters checked            : 1", batch_a.report)
        self.assertIn("absorbed records remaining : 0", batch_a.report)
        self.assertIn("Nothing lost, nothing duplicated.", batch_a.report)

        self._apply(batch_b)
        batch_b.action_verify()
        self.assertIn("masters checked            : 2", batch_b.report)
        self.assertIn("Nothing lost, nothing duplicated.", batch_b.report)

        # A is still verified against its own figures
        batch_a.action_verify()
        self.assertIn("masters checked            : 1", batch_a.report)
        self.assertIn("Nothing lost, nothing duplicated.", batch_a.report)

    def test_verify_without_stored_snapshot(self):
        self._hide_b()
        batch_a = self._batch("MERGE-002 legacy")
        self._apply(batch_a)
        # a batch analyzed before the snapshot was kept on its lines
        batch_a.line_ids.write({"snapshot_taken": False})
        with self.assertRaises(UserError):
            batch_a.action_verify()
