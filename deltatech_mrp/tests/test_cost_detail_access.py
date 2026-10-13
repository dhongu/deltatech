# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestCostDetailAccess(TransactionCase):
    """MRP-003: the cost detail SQL view follows the production company and is limited
    to the users that can read manufacturing orders."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "MRP-003 company B"})
        category = cls.env["product.category"].create({"name": "MRP-003 raw", "cost_categ": "raw"})
        finished = cls.env["product.product"].create({"name": "MRP-003 finished", "is_storable": True})
        component = cls.env["product.product"].create(
            {"name": "MRP-003 component", "is_storable": True, "categ_id": category.id}
        )
        cls.productions = {}
        for key, company in (("a", cls.company_a), ("b", cls.company_b)):
            env = cls.env(context=dict(cls.env.context, allowed_company_ids=company.ids))
            bom = env["mrp.bom"].create(
                {
                    "product_tmpl_id": finished.product_tmpl_id.id,
                    "product_qty": 1.0,
                    "company_id": company.id,
                    "bom_line_ids": [Command.create({"product_id": component.id, "product_qty": 2.0})],
                }
            )
            production = env["mrp.production"].create(
                {"product_id": finished.id, "bom_id": bom.id, "product_qty": 1.0, "company_id": company.id}
            )
            production.action_confirm()
            # the view only aggregates done component moves
            production.move_raw_ids.write({"state": "done"})
            cls.productions[key] = production
        cls.env.flush_all()
        cls.mrp_user_a = new_test_user(
            cls.env,
            login="mrp003_user_a",
            groups="base.group_user,mrp.group_mrp_user",
            company_id=cls.company_a.id,
            company_ids=[Command.set(cls.company_a.ids)],
        )
        cls.internal_user = new_test_user(
            cls.env,
            login="mrp003_internal",
            groups="base.group_user",
            company_id=cls.company_a.id,
            company_ids=[Command.set((cls.company_a | cls.company_b).ids)],
        )

    def test_cost_detail_company_field(self):
        for key, company in (("a", self.company_a), ("b", self.company_b)):
            details = self.env["deltatech.cost.detail"].search([("production_id", "=", self.productions[key].id)])
            self.assertTrue(details, key)
            self.assertEqual(details.company_id, company, key)

    def test_cost_detail_follows_company(self):
        details = self.env["deltatech.cost.detail"].with_user(self.mrp_user_a).search([])
        self.assertIn(self.productions["a"], details.production_id)
        self.assertNotIn(self.productions["b"], details.production_id)
        detail_b = self.env["deltatech.cost.detail"].search([("production_id", "=", self.productions["b"].id)])
        with self.assertRaises(AccessError):
            detail_b.with_user(self.mrp_user_a).read(["amount"])

    def test_cost_detail_on_production_form(self):
        production = self.productions["a"].with_user(self.mrp_user_a)
        self.assertTrue(production.cost_detail_ids)

    def test_internal_user_without_manufacturing_rights(self):
        with self.assertRaises(AccessError):
            self.env["deltatech.cost.detail"].with_user(self.internal_user).search([])
