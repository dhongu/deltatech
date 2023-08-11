# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestStockInventory(TransactionCase):
    def setUp(self):
        super(TestStockInventory, self).setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"name": self.partner_a.id})]
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

    def test_stock_change_product_qty(self):
        wizard = Form(
            self.env["stock.change.product.qty"]
            .with_user(self.inventory_user)
            .with_context(active_ids=self.product_a.ids)
        )
        wizard.product_id = self.product_a
        wizard.product_tmpl_id = self.product_a.product_tmpl_id
        wizard.new_quantity = 50
        wizard = wizard.save()
        wizard.with_user(self.inventory_user).change_product_qty()
