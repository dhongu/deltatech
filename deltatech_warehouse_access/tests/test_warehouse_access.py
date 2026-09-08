# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestWarehouseAccess(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        stock_user_group = cls.env.ref("stock.group_stock_user")
        cls.user_allowed = cls.env["res.users"].create(
            {
                "name": "Allowed User",
                "login": "wa_allowed_user",
                "group_ids": [(6, 0, [stock_user_group.id])],
            }
        )
        cls.user_denied = cls.env["res.users"].create(
            {
                "name": "Denied User",
                "login": "wa_denied_user",
                "group_ids": [(6, 0, [stock_user_group.id])],
            }
        )

        cls.warehouse = cls.env["stock.warehouse"].create(
            {
                "name": "Restricted Warehouse",
                "code": "RWH",
                "user_ids": [(6, 0, [cls.user_allowed.id])],
            }
        )
        cls.product = cls.env["product.product"].create({"name": "Test Product", "type": "consu"})
        cls.customer = cls.env["res.partner"].create({"name": "Test Customer"})

    def _new_picking(self):
        picking_type = self.warehouse.out_type_id
        return self.env["stock.picking"].create(
            {
                "partner_id": self.customer.id,
                "picking_type_id": picking_type.id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1.0,
                            "location_id": picking_type.default_location_src_id.id,
                            "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                        },
                    )
                ],
            }
        )

    def test_user_without_access_cannot_validate(self):
        picking = self._new_picking()
        picking.action_confirm()
        with self.assertRaises(AccessError):
            picking.with_user(self.user_denied).button_validate()

    def test_user_with_access_can_validate(self):
        picking = self._new_picking()
        picking.action_confirm()
        picking.with_user(self.user_allowed).button_validate()
        self.assertEqual(picking.state, "done")

    def test_warehouse_without_users_is_not_restricted(self):
        self.warehouse.user_ids = [(5, 0, 0)]
        picking = self._new_picking()
        picking.action_confirm()
        picking.with_user(self.user_denied).button_validate()
        self.assertEqual(picking.state, "done")
