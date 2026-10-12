# Copyright (C) 2026 Terrabit
# License OPL-1 (https://www.odoo.com/documentation/user/legal/licenses.html#odoo-apps).
from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestActivityRecordAccess(TransactionCase):
    """PICKACT-001: the activity journal follows the picking company and stock users
    can only read it; it is written by the logging itself."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "PICKACT-001 company B"})
        cls.product = cls.env["product.product"].create({"name": "PICKACT-001", "is_storable": True})
        cls.pickings = {}
        cls.records = {}
        for key, company in (("a", cls.company_a), ("b", cls.company_b)):
            env = cls.env(context=dict(cls.env.context, allowed_company_ids=company.ids))
            warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
            picking = env["stock.picking"].create(
                {
                    "picking_type_id": warehouse.out_type_id.id,
                    "location_id": warehouse.lot_stock_id.id,
                    "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                }
            )
            cls.pickings[key] = picking
            cls.records[key] = env["stock.picking.activity.record"].create(
                {"picking_id": picking.id, "user_id": cls.env.user.id, "activity_log": f"log {key}"}
            )
        cls.stock_user_a = new_test_user(
            cls.env,
            login="pickact001_user_a",
            groups="base.group_user,stock.group_stock_user",
            company_id=cls.company_a.id,
            company_ids=[Command.set(cls.company_a.ids)],
        )

    def test_company_field(self):
        self.assertEqual(self.records["a"].company_id, self.company_a)
        self.assertEqual(self.records["b"].company_id, self.company_b)

    def test_stock_user_reads_only_own_company(self):
        Records = self.env["stock.picking.activity.record"].with_user(self.stock_user_a)
        found = Records.search([])
        self.assertIn(self.records["a"], found)
        self.assertNotIn(self.records["b"], found)
        with self.assertRaises(AccessError):
            self.records["b"].with_user(self.stock_user_a).read(["activity_log"])

    def test_stock_user_cannot_forge_history(self):
        own = self.records["a"].with_user(self.stock_user_a)
        with self.assertRaises(AccessError):
            own.write({"user_id": self.env.user.id, "activity_log": "forged"})
        with self.assertRaises(AccessError):
            own.unlink()
        with self.assertRaises(AccessError):
            self.env["stock.picking.activity.record"].with_user(self.stock_user_a).create(
                {"picking_id": self.pickings["a"].id, "user_id": self.env.user.id}
            )
        self.assertEqual(self.records["a"].activity_log, "log a")

    def test_logging_still_works_for_stock_user(self):
        picking = self.pickings["a"].with_user(self.stock_user_a)
        picking.write({"origin": "PICKACT-001"})
        record = self.env["stock.picking.activity.record"].search(
            [("picking_id", "=", picking.id), ("user_id", "=", self.stock_user_a.id)]
        )
        self.assertEqual(len(record), 1)
        self.assertIn("PICKACT-001", record.activity_log)
        self.assertEqual(record.company_id, self.company_a)
