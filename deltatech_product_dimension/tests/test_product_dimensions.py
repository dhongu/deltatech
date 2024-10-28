# ©  2008-2019 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a product template
        self.product_template = self.env["product.template"].create(
            {
                "name": "Test Product Template",
                "type": "consu",
                "product_length": 2.5,
                "product_width": 1.5,
                "product_height": 3.0,
            }
        )

    def test_onchange_dimension(self):
        # Simulate onchange event for dimensions
        self.product_template.product_length = 100.0
        self.product_template.product_width = 100.0
        self.product_template.product_height = 100.0

        # Check that volume is computed correctly
        expected_volume = 100.0 * 100.0 * 100.0 / 1000000
        self.product_template._onchange_dimension()
        self.assertAlmostEqual(
            self.product_template.volume, expected_volume, places=6, msg="Volume should be computed correctly"
        )
