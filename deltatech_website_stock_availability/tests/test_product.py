# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests.common import TransactionCase

from odoo.addons.website_sale.tests.common import MockRequest


class TestProduct(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"partner_id": self.partner_a.id, "date_start": "2099-01-01", "delay": 5})]
        self.product_a = self.env["product.product"].create(
            {
                "name": "Test A",
                "is_storable": True,
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        self.product_b = self.env["product.product"].create(
            {
                "name": "Test B",
                "is_storable": True,
                # "inventory_availability": "preorder",
                "standard_price": 70,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        seller_ids = [(0, 0, {"partner_id": self.partner_a.id, "delay": 5})]
        self.product_c = self.env["product.product"].create(
            {
                "name": "Test C",
                "is_storable": True,
                # "inventory_availability": "preorder",
                "standard_price": 70,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )

        self.stock_location = self.env.ref("stock.stock_location_stock")

        self.env["stock.quant"]._update_available_quantity(self.product_a, self.stock_location, 1000)
        self.env["stock.quant"]._update_available_quantity(self.product_b, self.stock_location, 1000)

        # inv_line_a = {
        #     "product_id": self.product_a.id,
        #     "product_qty": 10000,
        #     "location_id": self.stock_location.id,
        # }

        # inventory = self.env["stock.inventory"].create(
        #     {
        #         "name": "Inv. productserial1",
        #         "line_ids": [
        #             (0, 0, inv_line_a),
        #         ],
        #     }
        # )
        # inventory.action_start()
        # inventory.action_validate()

    # def test_product(self):
    #     product = self.product_a
    #     self.assertIsNotNone(product.availability_text)
    #     product = self.product_b
    #     self.assertIsNotNone(product.availability_text)
    #     product = self.product_c
    #     self.assertIsNotNone(product.availability_text)

    def test_get_combination_info(self):
        website = self.env["website"].create({"name": "Test Website"})
        with MockRequest(self.env, website=website):
            product = self.product_b.product_tmpl_id.with_context(website_sale_stock_get_quantity=True)
            product._get_combination_info(product_id=self.product_b.id)

    def test_combination_info_includes_free_qty(self):
        # garda defensivă asigură free_qty în combination_info pentru template-urile QWeb
        website = self.env["website"].create({"name": "Test Website"})
        with MockRequest(self.env, website=website):
            tmpl = self.product_a.product_tmpl_id.with_context(website_sale_stock_get_quantity=True)
            info = tmpl._get_combination_info(product_id=self.product_a.id)
            self.assertIn("free_qty", info)
            self.assertGreater(info["free_qty"], 0, "Produsul A are 1000 în stoc")

    def test_combination_info_free_qty_guard_for_non_storable(self):
        # pentru produse non-storable core-ul O19 NU pune free_qty -> garda din modul
        # îl injectează prin website._get_product_available_qty (acoperă blocul defensiv)
        consu = self.env["product.product"].create(
            {"name": "Test Consu", "type": "consu", "is_storable": False, "list_price": 10}
        )
        website = self.env["website"].create({"name": "Test Website"})
        with MockRequest(self.env, website=website):
            tmpl = consu.product_tmpl_id.with_context(website_sale_stock_get_quantity=True)
            info = tmpl._get_combination_info(product_id=consu.id)
            self.assertIn("free_qty", info)
            self.assertEqual(info["free_qty"], 0)

    def test_combination_info_free_qty_zero_when_no_stock(self):
        # produsul C nu are stoc -> free_qty == 0 (nu lipsă/undefined)
        website = self.env["website"].create({"name": "Test Website"})
        with MockRequest(self.env, website=website):
            tmpl = self.product_c.product_tmpl_id.with_context(website_sale_stock_get_quantity=True)
            info = tmpl._get_combination_info(product_id=self.product_c.id)
            self.assertIn("free_qty", info)
            self.assertEqual(info["free_qty"], 0)

    def test_combination_info_sets_product_template(self):
        # product_template = id-ul template-ului, folosit de JS pentru scoping clase wrapper
        website = self.env["website"].create({"name": "Test Website"})
        with MockRequest(self.env, website=website):
            tmpl = self.product_a.product_tmpl_id.with_context(website_sale_stock_get_quantity=True)
            info = tmpl._get_combination_info(product_id=self.product_a.id)
            self.assertEqual(info.get("product_template"), self.product_a.product_tmpl_id.id)

    def test_combination_info_untouched_without_context(self):
        # fără contextul de stoc, modulul nu intervine (nu adaugă product_template)
        website = self.env["website"].create({"name": "Test Website"})
        with MockRequest(self.env, website=website):
            tmpl = self.product_a.product_tmpl_id
            info = tmpl._get_combination_info(product_id=self.product_a.id)
            self.assertNotIn("product_template", info)
