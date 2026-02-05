# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWebsitePublish(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ProductTemplate = cls.env["product.template"]

        # Creăm produse de test
        cls.product_1 = cls.ProductTemplate.create(
            {
                "name": "Test Product 1",
                "is_storable": True,
                "website_published": False,
            }
        )
        cls.product_2 = cls.ProductTemplate.create(
            {
                "name": "Test Product 2",
                "is_storable": True,
                "website_published": True,
            }
        )
        cls.product_3 = cls.ProductTemplate.create(
            {
                "name": "Test Product 3",
                "is_storable": True,
                "website_published": False,
            }
        )

    def test_action_website_publish(self):
        # Selectăm toate produsele de test
        products = self.product_1 | self.product_2 | self.product_3

        # Apelăm acțiunea de publicare
        products.action_website_publish()

        # Verificăm că toate sunt acum publicate
        self.assertTrue(self.product_1.website_published, "Produsul 1 ar trebui să fie publicat")
        self.assertTrue(self.product_2.website_published, "Produsul 2 ar trebui să rămână publicat")
        self.assertTrue(self.product_3.website_published, "Produsul 3 ar trebui să fie publicat")
