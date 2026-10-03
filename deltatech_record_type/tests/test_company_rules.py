# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestDefaultValuesCompanyRule(TransactionCase):
    """TYPE-001: record.type.default.values follow the company of their record type."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "TYPE-001 company B"})
        RecordType = cls.env["record.type"]
        Values = cls.env["record.type.default.values"]
        cls.type_a = RecordType.create({"name": "TYPE-001 A", "model": "sale.order", "company_id": cls.company_a.id})
        cls.type_b = RecordType.create({"name": "TYPE-001 B", "model": "sale.order", "company_id": cls.company_b.id})
        cls.type_shared = RecordType.create({"name": "TYPE-001 shared", "model": "sale.order"})
        cls.values = {}
        for key, record_type in (("a", cls.type_a), ("b", cls.type_b), ("shared", cls.type_shared)):
            cls.values[key] = Values.create(
                {
                    "record_type_id": record_type.id,
                    "field_name": "client_order_ref",
                    "field_value": f"TYPE-001 {key}",
                    "field_type": "char",
                }
            )
        cls.user_a = new_test_user(
            cls.env,
            login="type001_user_a",
            groups="base.group_user",
            company_id=cls.company_a.id,
            company_ids=[Command.set(cls.company_a.ids)],
        )

    def test_search_follows_record_type_company(self):
        found = self.env["record.type.default.values"].with_user(self.user_a).search([])
        self.assertIn(self.values["a"], found)
        self.assertIn(self.values["shared"], found)
        self.assertNotIn(self.values["b"], found)

    def test_other_company_values_read_write_unlink(self):
        other = self.values["b"].with_user(self.user_a)
        with self.assertRaises(AccessError):
            other.read(["field_value"])
        with self.assertRaises(AccessError):
            other.write({"field_value": "changed"})
        with self.assertRaises(AccessError):
            other.unlink()
        self.assertEqual(self.values["b"].field_value, "TYPE-001 b")

    def test_create_or_move_values_to_other_company(self):
        Values = self.env["record.type.default.values"].with_user(self.user_a)
        with self.assertRaises(AccessError):
            Values.create(
                {
                    "record_type_id": self.type_b.id,
                    "field_name": "client_order_ref",
                    "field_value": "forged",
                    "field_type": "char",
                }
            )
        with self.assertRaises(AccessError):
            self.values["a"].with_user(self.user_a).write({"record_type_id": self.type_b.id})

    def test_own_company_values_editable(self):
        own = self.values["a"].with_user(self.user_a)
        own.write({"field_value": "changed"})
        self.assertEqual(own.field_value, "changed")
