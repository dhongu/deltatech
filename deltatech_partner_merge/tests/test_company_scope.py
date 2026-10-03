# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestCompanyScope(TransactionCase):
    """MERGE-001: the bulk merge stays inside the caller's companies and never merges
    partners of different companies."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "MERGE-001 company B"})
        Partner = cls.env["res.partner"]

        def partner(name, vat, company):
            return Partner.create({"name": name, "vat": vat, "is_company": True, "company_id": company and company.id})

        # same VAT inside company A and inside company B
        cls.a1 = partner("Merge Scope Alpha SRL", "RO90000001", cls.company_a)
        cls.a2 = partner("Merge Scope Alpha S.R.L.", "RO 90000001", cls.company_a)
        cls.b1 = partner("Merge Scope Alpha SRL", "RO90000001", cls.company_b)
        cls.b2 = partner("Merge Scope Alpha S.R.L.", "RO90000001", cls.company_b)
        # same VAT on one partner of A and one of B: not a duplicate
        cls.x_a = partner("Merge Scope Beta SRL", "RO90000002", cls.company_a)
        cls.x_b = partner("Merge Scope Beta SRL", "RO90000002", cls.company_b)
        # shared partners (no company)
        cls.s1 = partner("Merge Scope Gamma SRL", "RO90000003", False)
        cls.s2 = partner("Merge Scope Gamma S.R.L.", "RO90000003", False)
        cls.ours = cls.a1 | cls.a2 | cls.b1 | cls.b2 | cls.x_a | cls.x_b | cls.s1 | cls.s2

        cls.operator_a = new_test_user(
            cls.env,
            login="merge001_operator_a",
            groups="base.group_user,base.group_partner_manager,deltatech_partner_merge.group_partner_merge_apply",
            company_id=cls.company_a.id,
            company_ids=[Command.set(cls.company_a.ids)],
        )
        cls.operator_no_rights = new_test_user(
            cls.env,
            login="merge001_operator_no_rights",
            groups="base.group_user,deltatech_partner_merge.group_partner_merge_apply",
            company_id=cls.company_a.id,
            company_ids=[Command.set(cls.company_a.ids)],
        )
        cls.env.flush_all()

    def _batch(self, env):
        return env["partner.merge.batch"].create({"name": "MERGE-001", "category_ids": "A,B", "group_limit": 0})

    def _our_lines(self, batch):
        return batch.line_ids.filtered(lambda line: line.master_id in self.ours)

    def _absorbed(self, line):
        return self.env["res.partner"].browse([int(i) for i in line.absorbed_ids.split(", ")])

    def _admin_env(self):
        return self.env(context=dict(self.env.context, allowed_company_ids=(self.company_a | self.company_b).ids))

    def test_operator_sees_only_own_company(self):
        batch = self._batch(self.env(user=self.operator_a))
        batch.action_analyze()
        lines = self._our_lines(batch)
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines.master_id | self._absorbed(lines), self.a1 | self.a2)
        self.assertEqual(lines.company_id, self.company_a)

    def test_groups_never_mix_companies(self):
        batch = self._batch(self._admin_env())
        batch.action_analyze()
        lines = self._our_lines(batch)
        groups = {frozenset((line.master_id | self._absorbed(line)).ids) for line in lines}
        self.assertEqual(
            groups,
            {
                frozenset((self.a1 | self.a2).ids),
                frozenset((self.b1 | self.b2).ids),
                frozenset((self.s1 | self.s2).ids),
            },
        )
        for line in lines:
            self.assertEqual(self._absorbed(line).company_id, line.master_id.company_id)

    def test_apply_rejects_batch_outside_scope(self):
        batch = self._batch(self._admin_env())
        batch.action_analyze()
        batch.action_simulate()
        with self.assertRaises(UserError):
            batch.with_user(self.operator_a).action_apply()
        self.assertTrue(self.b2.exists() and self.b1.exists())

    def test_apply_requires_partner_rights(self):
        batch = self._batch(self.env(user=self.operator_no_rights))
        batch.action_analyze()
        batch.action_simulate()
        with self.assertRaises(AccessError):
            batch.action_apply()

    def test_operator_applies_own_company(self):
        batch = self._batch(self.env(user=self.operator_a))
        batch.archive_instead_of_delete = True
        batch.action_analyze()
        batch.action_simulate()
        batch.action_apply()
        self.assertEqual(batch.state, "done")
        self.env.invalidate_all()
        self.assertEqual(len((self.a1 | self.a2).filtered("active")), 1)
        self.assertTrue(all((self.b1 | self.b2 | self.x_a | self.x_b | self.s1 | self.s2).mapped("active")))
