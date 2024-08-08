# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestStockInventory(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"partner_id": self.partner_a.id})]
        self.product_a = self.env["product.product"].create(
            {"name": "Test A", "type": "product", "standard_price": 100, "list_price": 150, "seller_ids": seller_ids}
        )
        self.product_b = self.env["product.product"].create(
            {"name": "Test B", "type": "product", "standard_price": 70, "list_price": 150, "seller_ids": seller_ids}
        )
        # self.stock_location = self.env.ref("stock.stock_location_stock")
        self.stock_location = self.env["stock.location"].create({"name": "Test location", "usage": "internal"})
        # Create a user with rights
        group_inventory_user = self.env.ref("deltatech_stock_inventory.group_view_inventory_button")
        group_stock_manager = self.env.ref("stock.group_stock_manager")

        self.inventory_user = (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Inv user",
                    "login": "invUser",
                    "email": "inv@odoo.com",
                    "groups_id": [(6, 0, [group_inventory_user.id, group_stock_manager.id])],
                }
            )
        )
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
            }
        )
        self.quant = self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.stock_location.id,
                "quantity": 10.0,
            }
        )

        self.inventory_1 = self.env["stock.inventory"].create(
            {
                "name": "Inventory 1",
                "location_ids": [(6, 0, [self.stock_location.id])],
                "state": "done",
            }
        )

        self.inventory_2 = self.env["stock.inventory"].create(
            {
                "name": "Inventory 2",
                "location_ids": [(6, 0, [self.stock_location.id])],
                "state": "done",
            }
        )

    def test_stock_inventory(self):
        inv_line_a = {
            "product_id": self.product_a.id,
            "product_qty": 10000,
            "location_id": self.stock_location.id,
        }
        inv_line_b = {
            "product_id": self.product_b.id,
            "product_qty": 10000,
            "location_id": self.stock_location.id,
        }
        inventory = (
            self.env["stock.inventory"]
            .with_user(self.inventory_user)
            .create(
                {
                    "name": "Inv. productserial1",
                    "line_ids": [
                        (0, 0, inv_line_a),
                        (0, 0, inv_line_b),
                    ],
                }
            )
        )
        inventory.with_user(self.inventory_user).action_start()
        inventory.with_user(self.inventory_user).action_validate()

    # def test_action_update_quantity_on_hand(self):
    #     self.product_b.product_tmpl_id.action_update_quantity_on_hand()

    # def test_get_last_inventory_date(self):
    #     self.product_a.product_tmpl_id.get_last_inventory_date()

    # def test_confirm_actual_inventory(self):
    #     self.product_b.product_tmpl_id.confirm_actual_inventory()

    def test_new_inventory(self):
        inventory = (
            self.env["stock.inventory"]
            .with_user(self.inventory_user)
            .create({"location_ids": [(6, 0, self.stock_location.ids)]})
        )
        inventory.with_user(self.inventory_user).action_start()

    def test_stock_inventory_merge(self):
        inv_line_a = {
            "product_id": self.product_a.id,
            "product_qty": 10000,
            "location_id": self.stock_location.id,
        }
        inv_line_b = {
            "product_id": self.product_b.id,
            "product_qty": 10000,
            "location_id": self.stock_location.id,
        }
        inventory_a = (
            self.env["stock.inventory"]
            .with_user(self.inventory_user)
            .create(
                {
                    "name": "Inv. productserial1",
                    "line_ids": [
                        (0, 0, inv_line_a),
                    ],
                }
            )
        )
        inventory_a.with_user(self.inventory_user).action_start()
        inventory_b = (
            self.env["stock.inventory"]
            .with_user(self.inventory_user)
            .create(
                {
                    "name": "Inv. productserial1",
                    "line_ids": [
                        (0, 0, inv_line_b),
                    ],
                }
            )
        )
        inventory_b.with_user(self.inventory_user).action_start()
        active_ids = [inventory_a.id, inventory_b.id]
        wizard = Form(self.env["stock.inventory.merge"])
        wizard = wizard.save()
        with self.assertRaises(UserError):
            wizard.with_context(active_ids=active_ids).merge_inventory()

    def test_stock_quant_inventory(self):
        quant = self.env["stock.quant"].create(
            {
                "product_id": self.product_a.id,
                "location_id": self.stock_location.id,
                "quantity": 100,
                "inventory_quantity": 100,
            }
        )
        quant.create_inventory_lines()
        quant.inventory_quantity = 100
        quant.action_apply_inventory()

    def test_product_loc(self):
        self.product_a.product_tmpl_id.loc_row = "A"

    def test_merge_inventory(self):
        # Create the stock.inventory.merge record
        merge_wizard = self.env["stock.inventory.merge"].create(
            {
                "name": "Merged Inventory",
                "date": fields.Datetime.now(),
                "company_id": self.env.user.company_id.id,
                "location_id": self.stock_location.id,
            }
        )

        # Call the merge_inventory method
        merge_wizard.with_context(active_ids=[self.inventory_1.id, self.inventory_2.id]).merge_inventory()

        # Get the created inventory
        merged_inventory = self.env["stock.inventory"].search([], order="id desc", limit=1)

        # Check that the inventory was created with the correct name and date
        self.assertEqual(merged_inventory.name, merge_wizard.name)
        self.assertEqual(merged_inventory.date, merge_wizard.date)
        self.assertEqual(merged_inventory.state, "done")
