# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestInventoryCompanyRules(TransactionCase):
    """INVENTORY-003: inventory documents and lines follow the allowed companies."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "INVENTORY-003 company B"})
        product = cls.env["product.product"].create({"name": "INVENTORY-003", "is_storable": True})
        cls.docs = {}
        cls.lines = {}
        for key, company in (("a", cls.company_a), ("b", cls.company_b)):
            env = cls.env(context=dict(cls.env.context, allowed_company_ids=company.ids))
            location = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1).lot_stock_id
            inventory = env["stock.inventory"].create(
                {"name": f"INVENTORY-003 {key}", "company_id": company.id, "location_ids": [Command.set(location.ids)]}
            )
            cls.docs[key] = inventory
            cls.lines[key] = env["stock.inventory.line"].create(
                {
                    "inventory_id": inventory.id,
                    "product_id": product.id,
                    "product_uom_id": product.uom_id.id,
                    "location_id": location.id,
                    "product_qty": 5.0,
                }
            )
        cls.stock_user_a = new_test_user(
            cls.env,
            login="inventory003_user_a",
            groups="base.group_user,stock.group_stock_manager",
            company_id=cls.company_a.id,
            company_ids=[Command.set(cls.company_a.ids)],
        )

    def test_search_follows_company(self):
        docs = self.env["stock.inventory"].with_user(self.stock_user_a).search([])
        self.assertIn(self.docs["a"], docs)
        self.assertNotIn(self.docs["b"], docs)
        lines = self.env["stock.inventory.line"].with_user(self.stock_user_a).search([])
        self.assertIn(self.lines["a"], lines)
        self.assertNotIn(self.lines["b"], lines)

    def test_other_company_read_write_unlink(self):
        for record in (self.docs["b"], self.lines["b"]):
            other = record.with_user(self.stock_user_a)
            with self.assertRaises(AccessError, msg=record._name):
                other.read(["company_id"])
            with self.assertRaises(AccessError, msg=record._name):
                other.write({"name": "changed"} if record._name == "stock.inventory" else {"product_qty": 1.0})
            with self.assertRaises(AccessError, msg=record._name):
                other.unlink()
        self.assertEqual(self.lines["b"].product_qty, 5.0)

    def test_create_in_other_company(self):
        with self.assertRaises(AccessError):
            self.env["stock.inventory"].with_user(self.stock_user_a).create(
                {"name": "forged", "company_id": self.company_b.id}
            )

    def test_own_company_still_editable(self):
        self.lines["a"].with_user(self.stock_user_a).write({"product_qty": 7.0})
        self.assertEqual(self.lines["a"].product_qty, 7.0)
