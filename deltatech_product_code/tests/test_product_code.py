# ©  2023Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestProductCode(TransactionCase):
    def setUp(self):
        super().setUp()

        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        # pregatire categorie noua pentru test in care se sa fie definita secventa de coduri

        # creare secventa de coduri
        sequence = self.env["ir.sequence"].create(
            {
                "name": "Product Code",
                "code": "product.code",
                "prefix": "TEST/",
                "padding": 4,
                "number_increment": 1,
                "implementation": "standard",
            }
        )
        # creare categorie noua
        self.product_category = self.env["product.category"].create(
            {
                "name": "Test",
                "sequence_id": sequence.id,
                "generate_barcode": True,
            }
        )

    def test_new_product_template(self):
        # creare produs nou
        product_template = self.env["product.template"].create(
            {
                "name": "Test",
                "categ_id": self.product_category.id,
            }
        )
        # verificare daca a fost generat codul
        self.assertEqual(product_template.default_code, "TEST/0001")

    def test_new_product_product(self):
        # creare produs nou
        product_product = self.env["product.product"].create(
            {
                "name": "Test",
                "categ_id": self.product_category.id,
            }
        )
        # verificare daca a fost generat codul
        self.assertEqual(product_product.default_code, "TEST/0001")

    def test_show_duplicate(self):
        self.env["product.template"].show_not_unique()

    def test_now_product_with_barcode(self):
        self.product_category.write({"generate_barcode": True})
        product_template = self.env["product.template"].create(
            {
                "name": "Test",
                "categ_id": self.product_category.id,
            }
        )
        self.assertTrue(product_template.barcode)
