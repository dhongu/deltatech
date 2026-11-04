from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestProductCostChange(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref("stock.warehouse0").lot_stock_id
        # the core create passes valuation_date to _change_standard_price (Odoo 20 signature)
        cls.product = cls.env["product.product"].create(
            {"name": "Cost Product", "is_storable": True, "standard_price": 10.0}
        )
        cls.stock_user = new_test_user(
            cls.env,
            login="cost_stock_user",
            groups="base.group_user,stock.group_stock_manager,product.group_product_manager",
        )

    def test_create_with_cost(self):
        self.assertEqual(self.product.standard_price, 10.0)

    def test_change_cost_without_stock_allowed(self):
        self.product.with_user(self.stock_user).standard_price = 12.0
        self.assertEqual(self.product.standard_price, 12.0)

    def test_change_cost_with_stock_refused(self):
        self.env["stock.quant"]._update_available_quantity(self.product, self.stock_location, 5)
        with self.assertRaises(AccessError):
            self.product.with_user(self.stock_user).standard_price = 12.0

    def test_change_cost_with_stock_by_group(self):
        self.env["stock.quant"]._update_available_quantity(self.product, self.stock_location, 5)
        self.stock_user.group_ids |= self.env.ref("deltatech_stock_account.group_change_product_price")
        self.product.with_user(self.stock_user).standard_price = 12.0
        self.assertEqual(self.product.standard_price, 12.0)
