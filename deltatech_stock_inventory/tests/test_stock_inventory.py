# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


def _create_accounting_data(env):
    """Create the accounts and journals used in stock valuation.

    :param env: environment used to create the records
    :return: an input account, an output account, a valuation account, an expense account, a stock journal
    """
    stock_input_account = env["account.account"].create(
        {
            "name": "Stock Input",
            "code": "StockIn",
            "user_type_id": env.ref("account.data_account_type_current_assets").id,
            "reconcile": True,
        }
    )
    stock_output_account = env["account.account"].create(
        {
            "name": "Stock Output",
            "code": "StockOut",
            "user_type_id": env.ref("account.data_account_type_current_assets").id,
            "reconcile": True,
        }
    )
    stock_valuation_account = env["account.account"].create(
        {
            "name": "Stock Valuation",
            "code": "Stock Valuation",
            "user_type_id": env.ref("account.data_account_type_current_assets").id,
            "reconcile": True,
        }
    )
    expense_account = env["account.account"].create(
        {
            "name": "Expense Account",
            "code": "Expense Account",
            "user_type_id": env.ref("account.data_account_type_expenses").id,
            "reconcile": True,
        }
    )
    stock_journal = env["account.journal"].create(
        {
            "name": "Stock Journal",
            "code": "STJTEST",
            "type": "general",
        }
    )
    return stock_input_account, stock_output_account, stock_valuation_account, expense_account, stock_journal


class TestStockInventory(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})
        (
            self.stock_input_account,
            self.stock_output_account,
            self.stock_valuation_account,
            self.expense_account,
            self.stock_journal,
        ) = _create_accounting_data(self.env)
        self.category_average = self.env["product.category"].create(
            {"name": "category1", "property_cost_method": "average", "property_valuation": "real_time"}
        )
        self.category_fifo = self.env["product.category"].create(
            {"name": "category2", "property_cost_method": "fifo", "property_valuation": "real_time"}
        )
        self.category_average.write(
            {
                "property_stock_account_input_categ_id": self.stock_input_account.id,
                "property_stock_account_output_categ_id": self.stock_output_account.id,
                "property_stock_valuation_account_id": self.stock_valuation_account.id,
                "property_stock_journal": self.stock_journal.id,
            }
        )
        self.category_fifo.write(
            {
                "property_stock_account_input_categ_id": self.stock_input_account.id,
                "property_stock_account_output_categ_id": self.stock_output_account.id,
                "property_stock_valuation_account_id": self.stock_valuation_account.id,
                "property_stock_journal": self.stock_journal.id,
            }
        )
        seller_ids = [(0, 0, {"name": self.partner_a.id})]
        self.product_a = self.env["product.product"].create(
            {
                "name": "Test A",
                "type": "product",
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
                "categ_id": self.category_average.id,
            }
        )
        self.product_b = self.env["product.product"].create(
            {
                "name": "Test B",
                "type": "product",
                "standard_price": 70,
                "list_price": 150,
                "seller_ids": seller_ids,
                "categ_id": self.category_fifo.id,
            }
        )
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

    def test_stock_inventory_svl(self):
        self.test_stock_inventory()
        # second inventory, with price and archive svl
        self.env["ir.config_parameter"].create(
            {
                "key": "stock.use_inventory_price",
                "value": True,
            }
        )
        inv_line_c = {
            "product_id": self.product_a.id,
            "product_qty": 1,
            "standard_price": 33,
            "location_id": self.stock_location.id,
        }
        inv_line_d = {
            "product_id": self.product_b.id,
            "product_qty": 1,
            "standard_price": 20,
            "location_id": self.stock_location.id,
        }
        inventory = (
            self.env["stock.inventory"]
            .with_user(self.inventory_user)
            .create(
                {
                    "name": "Inv. 2",
                    "archive_svl": True,
                    "line_ids": [
                        (0, 0, inv_line_c),
                        (0, 0, inv_line_d),
                    ],
                }
            )
        )
        inventory.with_user(self.inventory_user).action_start()
        inventory.with_user(self.inventory_user).action_validate()
        domain = [("product_id", "in", [self.product_a.id, self.product_b.id])]
        svls = self.env["stock.valuation.layer"].with_context(active_test=True).search(domain)
        svls_value = 0.0
        for svl in svls:
            svls_value += svl.value
        self.assertEqual(svls_value, 200013.0)

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
        wizard.with_context(active_ids=active_ids).merge_inventory

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

    # @tagged("post_install")
    # def test_inventory_svl(self):
    #     inv_line_a = {
    #         "product_id": self.product_a.id,
    #         "product_qty": 2,
    #         "location_id": self.stock_location.id,
    #     }
    #     inv_line_b = {
    #         "product_id": self.product_b.id,
    #         "product_qty": 2,
    #         "location_id": self.stock_location.id,
    #     }
    #     inventory = (
    #         self.env["stock.inventory"]
    #         .with_user(self.inventory_user)
    #         .create(
    #             {
    #                 "name": "Inv. productserial1",
    #                 "line_ids": [
    #                     (0, 0, inv_line_a),
    #                     (0, 0, inv_line_b),
    #                 ],
    #             }
    #         )
    #     )
    #     inventory.with_user(self.inventory_user).action_start()
    #     inventory.with_user(self.inventory_user).action_validate()
    #     domain = [("product_id", "in", [self.product_a.id, self.product_b.id,])]
    #     svls = self.env["stock.valuation.layer"].search(domain)
    #     svls_value = 0.0
    #     for svl in svls:
    #         svls_value += svl.value
    #     inv_line_a = {
    #         "product_id": self.product_a.id,
    #         "product_qty": 2,
    #         "location_id": self.stock_location.id,
    #     }
    #     inv_line_b = {
    #         "product_id": self.product_b.id,
    #         "product_qty": 2,
    #         "location_id": self.stock_location.id,
    #     }
    #     inventory = (
    #         self.env["stock.inventory"]
    #         .with_user(self.inventory_user)
    #         .create(
    #             {
    #                 "name": "Inv. productserial1",
    #                 "line_ids": [
    #                     (0, 0, inv_line_a),
    #                     (0, 0, inv_line_b),
    #                 ],
    #             }
    #         )
    #     )
    #     inventory.with_user(self.inventory_user).action_start()
    #     inventory.with_user(self.inventory_user).action_validate()
