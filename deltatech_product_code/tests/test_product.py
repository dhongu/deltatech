# ©  2015-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestProductCode(TransactionCase):
    # se defineste o secventa pentru codificare  si categorie de produs
    def setUp(self):
        super().setUp()
        self.sequence = self.env["ir.sequence"].create(
            {"name": "Test sequence", "implementation": "no_gap", "prefix": "TEST", "padding": 4}
        )
        self.categ = self.env["product.category"].create(
            {"name": "Test category", "sequence_id": self.sequence.id, "generate_barcode": True}
        )

    # se testeaza crearea unui produs
    def test_product_template(self):
        product = Form(self.env["product.template"])
        product.name = "Test product"
        product.categ_id = self.categ
        product = product.save()
        self.assertEqual(product.default_code, "TEST0001")

        # se verifica daca a fost generat un cod de bare aleatoriu
        self.assertTrue(product.barcode.startswith("40"))
        self.assertEqual(len(product.barcode), 13)

    # se testeaza crearea unui produs cu cod de bare
    def test_product_template_barcode(self):
        product = Form(self.env["product.template"])
        product.name = "Test product"
        product.categ_id = self.categ
        product.barcode = "1234567890123"
        product = product.save()
        self.assertEqual(product.default_code, "TEST0001")
        self.assertEqual(product.barcode, "1234567890123")

    # se testeaza crearea unei variante de produs
    def test_product_product(self):
        product = Form(self.env["product.product"])
        product.name = "Test product"
        product.categ_id = self.categ
        product = product.save()
        self.assertEqual(product.default_code, "TEST0001")

        # se verifica daca a fost generat un cod de bare aleatoriu
        self.assertTrue(product.barcode.startswith("40"))
        self.assertEqual(len(product.barcode), 13)
