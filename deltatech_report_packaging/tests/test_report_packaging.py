from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPackagingMaterial(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_a.product_tmpl_id.packaging_material_ids = [
            Command.create({"material_type": "plastic", "qty": 1.0}),
            Command.create({"material_type": "wood", "qty": 0.5}),
            Command.create({"material_type": "glass", "qty": 0.25}),
        ]

    def _create_invoice(self, quantity=2.0):
        return self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "quantity": quantity,
                            "price_unit": 100.0,
                            "tax_ids": [Command.clear()],
                        }
                    )
                ],
            }
        )

    def test_post_computes_packaging_materials(self):
        invoice = self._create_invoice()

        invoice.action_post()

        quantities = {line.material_type: line.qty for line in invoice.packaging_material_ids}
        self.assertEqual(
            quantities,
            {"plastic": 2.0, "wood": 1.0, "glass": 0.5},
        )

    def test_refresh_replaces_previous_values(self):
        invoice = self._create_invoice()
        invoice.refresh_packaging_material()
        invoice.invoice_line_ids.quantity = 4.0

        invoice.refresh_packaging_material()

        quantities = {line.material_type: line.qty for line in invoice.packaging_material_ids}
        self.assertEqual(
            quantities,
            {"plastic": 4.0, "wood": 2.0, "glass": 1.0},
        )

    def test_report_aggregates_invoices_and_supports_all_material_types(self):
        invoices = self._create_invoice(2.0) | self._create_invoice(3.0)
        report = self.env["packaging.report.material"].with_context(active_ids=invoices.ids).create({})

        action = report.do_report()

        quantities = {line.material_type: line.qty for line in report.line_ids}
        self.assertEqual(
            quantities,
            {"plastic": 5.0, "wood": 2.5, "glass": 1.25},
        )
        self.assertEqual(report.state, "get")
        self.assertEqual(action["res_id"], report.id)
