# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
import json

from odoo.tests.common import TransactionCase


class TestProductList(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.ref("base.main_company")
        self.product_list = self.env["product.list"].create(
            {
                "name": "Test Product List",
                "products_domain": json.dumps([["sale_ok", "=", True]]),
                "active": True,
                "limit": 80,
                "company_id": self.company.id,
            }
        )

    def test_product_list_creation(self):
        self.assertEqual(self.product_list.name, "Test Product List")
        self.assertEqual(json.loads(self.product_list.products_domain), [["sale_ok", "=", True]])
        self.assertTrue(self.product_list.active)
        self.assertEqual(self.product_list.limit, 80)
        self.assertEqual(self.product_list.company_id, self.company)
