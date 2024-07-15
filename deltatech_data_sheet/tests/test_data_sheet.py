from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create necessary records for the test
        self.attachment_1 = self.env["ir.attachment"].create(
            {
                "name": "Test Data Sheet",
                "mimetype": "application/pdf",
                "public": True,
            }
        )

        self.attachment_2 = self.env["ir.attachment"].create(
            {
                "name": "Test Safety Data Sheet",
                "mimetype": "application/pdf",
                "public": True,
            }
        )

        self.product_template = self.env["product.template"].create(
            {
                "name": "Test Product",
                "data_sheet_id": self.attachment_1.id,
                "safety_data_sheet_id": self.attachment_2.id,
            }
        )

    def test_product_template(self):
        # Check that the product template was created with the correct data sheet and safety data sheet
        self.assertEqual(self.product_template.data_sheet_id, self.attachment_1)
        self.assertEqual(self.product_template.safety_data_sheet_id, self.attachment_2)
