# ©  2015-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product_a = self.env["product.template"].create(
            {"name": "Test A", "type": "product", "standard_price": 100, "list_price": 150}
        )

    def test_product_template(self):
        self.product_a.product_length = 100
        self.product_a.product_width = 100
        self.product_a.product_height = 100
        self.assertEqual(self.product_a.volume, 1)

    def test_product_template_form(self):
        form = Form(self.product_a)
        form.product_length = 100
        form.product_width = 100
        form.product_height = 100
        self.assertEqual(form.volume, 1)
