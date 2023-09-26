# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestInvoice(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        sequence = self.env["ir.sequence"].create(
            {
                "name": "Test",
                "code": "test",
                "prefix": "TEST",
                "padding": 4,
                "number_increment": 1,
                "use_date_range": True,
            }
        )
        self.category = self.env["product.category"].create(
            {
                "name": "Test",
                "sequence_id": sequence.id,
                "generate_barcode": True,
            }
        )

    def test_create_product(self):
        seller_ids = [(0, 0, {"name": self.partner_a.id})]
        self.product_a = self.env["product.product"].create(
            {
                "name": "Test A",
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
                "categ_id": self.category.id,
            }
        )
        self.assertEqual(self.product_a.default_code, "TEST0001")
        self.product_b = self.env["product.product"].create(
            {
                "name": "Test B",
                "standard_price": 70,
                "list_price": 150,
                "seller_ids": seller_ids,
                "categ_id": self.category.id,
            }
        )
        self.assertEqual(self.product_b.default_code, "TEST0002")

    def test_create_product_template(self):
        seller_ids = [(0, 0, {"name": self.partner_a.id})]
        self.product_a = self.env["product.template"].create(
            {
                "name": "Test A",
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
                "categ_id": self.category.id,
            }
        )
        self.assertEqual(self.product_a.default_code, "TEST0001")
        self.product_b = self.env["product.template"].create(
            {
                "name": "Test B",
                "standard_price": 70,
                "list_price": 150,
                "seller_ids": seller_ids,
                "categ_id": self.category.id,
            }
        )
        self.assertEqual(self.product_b.default_code, "TEST0002")

    def test_create_product_form(self):
        product = Form(self.env["product.product"])
        product.name = "Test A"
        product = product.save()
        product.categ_id = self.category.id
        product.button_new_code()

    def test_show_not_unique(self):
        self.env["product.template"].show_not_unique()
