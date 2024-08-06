from odoo.tests.common import TransactionCase


class TestPackagingMaterial(TransactionCase):
    def setUp(self):
        super().setUp()
        self.AccountMove = self.env["account.move"]
        self.ProductTemplate = self.env["product.template"]
        self.PackagingProductMaterial = self.env["packaging.product.material"]
        self.PackagingInvoiceMaterial = self.env["packaging.invoice.material"]
        self.PackagingReportMaterial = self.env["packaging.report.material"]

        # Create a product template with packaging materials
        self.product_template = self.ProductTemplate.create(
            {
                "name": "Test Product",
                "default_code": "TEST_PRODUCT",
                "packaging_material_ids": [
                    (0, 0, {"material_type": "plastic", "qty": 1.0}),
                    (0, 0, {"material_type": "wood", "qty": 0.5}),
                ],
            }
        )

        # Create an invoice with the product
        self.invoice = self.AccountMove.create(
            {
                "move_type": "out_invoice",
                "partner_id": self.env.ref("base.res_partner_1").id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_template.product_variant_id.id,
                            "quantity": 2,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

    def test_refresh_packaging_material(self):
        self.invoice.action_post()
        self.invoice.refresh_packaging_material()

        # Verify packaging materials have been calculated and linked to the invoice
        packaging_materials = self.PackagingInvoiceMaterial.search([("invoice_id", "=", self.invoice.id)])
        self.assertEqual(len(packaging_materials), 2)
        self.assertEqual(packaging_materials[0].material_type, "plastic")
        self.assertEqual(packaging_materials[0].qty, 2.0)
        self.assertEqual(packaging_materials[1].material_type, "wood")
        self.assertEqual(packaging_materials[1].qty, 1.0)

    def test_do_report(self):
        self.invoice.action_post()
        self.invoice.refresh_packaging_material()

        # Create a packaging report
        report = self.PackagingReportMaterial.create({})
        report.do_report()
