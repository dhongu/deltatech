# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests.common import TransactionCase


class TestProduct(TransactionCase):
    def setUp(self):
        super(TestProduct, self).setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"name": self.partner_a.id, "date_start": "2099-01-01", "delay": 5})]
        self.product_a = self.env["product.product"].create(
            {
                "name": "Test A",
                "type": "product",
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        self.product_b = self.env["product.product"].create(
            {
                "name": "Test B",
                "type": "product",
                "inventory_availability": "preorder",
                "standard_price": 70,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        seller_ids = [(0, 0, {"name": self.partner_a.id, "delay": 5})]
        self.product_c = self.env["product.product"].create(
            {
                "name": "Test C",
                "type": "product",
                "inventory_availability": "preorder",
                "standard_price": 70,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )

        self.stock_location = self.env["ir.model.data"].xmlid_to_object("stock.stock_location_stock")
        inv_line_a = {
            "product_id": self.product_a.id,
            "product_qty": 10000,
            "location_id": self.stock_location.id,
        }

        inventory = self.env["stock.inventory"].create(
            {
                "name": "Inv. productserial1",
                "line_ids": [
                    (0, 0, inv_line_a),
                ],
            }
        )
        inventory.action_start()
        inventory.action_validate()

    def test_product(self):
        product = self.product_a
        self.assertIsNotNone(product.availability_text)
        product = self.product_b
        self.assertIsNotNone(product.availability_text)
        product = self.product_c
        self.assertIsNotNone(product.availability_text)

    def test_get_combination_info(self):
        product = self.product_b.product_tmpl_id.with_context(website_sale_stock_get_quantity=True)
        product._get_combination_info(product_id=self.product_b.id)
