# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRecordTypeAccessRights(TransactionCase):
    """TYPE-002: internal users only read record types and their default values;
    the sales / purchase / accounting managers maintain them."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.record_type = cls.env["record.type"].create({"name": "TYPE-002", "model": "sale.order"})
        cls.value = cls.env["record.type.default.values"].create(
            {
                "record_type_id": cls.record_type.id,
                "field_name": "client_order_ref",
                "field_value": "TYPE-002",
                "field_type": "char",
            }
        )
        cls.employee = new_test_user(cls.env, login="type002_employee", groups="base.group_user")
        cls.managers = [
            new_test_user(cls.env, login="type002_sale_manager", groups="sales_team.group_sale_manager"),
            new_test_user(cls.env, login="type002_purchase_manager", groups="purchase.group_purchase_manager"),
            new_test_user(cls.env, login="type002_account_manager", groups="account.group_account_manager"),
        ]

    def test_internal_user_read_only(self):
        record_type = self.record_type.with_user(self.employee)
        value = self.value.with_user(self.employee)
        self.assertEqual(record_type.name, "TYPE-002")
        self.assertEqual(value.field_value, "TYPE-002")
        with self.assertRaises(AccessError):
            record_type.write({"name": "changed"})
        with self.assertRaises(AccessError):
            value.write({"field_value": "changed"})
        with self.assertRaises(AccessError):
            self.env["record.type"].with_user(self.employee).create({"name": "forged", "model": "sale.order"})
        with self.assertRaises(AccessError):
            self.env["record.type.default.values"].with_user(self.employee).create(
                {
                    "record_type_id": self.record_type.id,
                    "field_name": "client_order_ref",
                    "field_value": "forged",
                    "field_type": "char",
                }
            )
        with self.assertRaises(AccessError):
            value.unlink()
        with self.assertRaises(AccessError):
            record_type.unlink()

    def test_managers_maintain_types(self):
        for manager in self.managers:
            record_type = (
                self.env["record.type"].with_user(manager).create({"name": manager.login, "model": "sale.order"})
            )
            value = (
                self.env["record.type.default.values"]
                .with_user(manager)
                .create(
                    {
                        "record_type_id": record_type.id,
                        "field_name": "client_order_ref",
                        "field_value": manager.login,
                        "field_type": "char",
                    }
                )
            )
            record_type.write({"name": f"{manager.login} changed"})
            value.write({"field_value": "changed"})
            value.unlink()
            record_type.unlink()
