# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import tagged

from odoo.addons.deltatech_sale_commission.tests.test_sale import TestSaleCommissionBase


@tagged("post_install", "-at_install")
class TestSaleMarginReportManufacturer(TestSaleCommissionBase):
    def test_manufacturer_in_margin_report(self):
        manufacturer = self.env["res.partner"].create({"name": "Manufacturer TEST", "is_manufacturer": True})
        self.product_a.manufacturer_id = manufacturer
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_line_ids": [(0, 0, {"product_id": self.product_a.id, "quantity": 2, "price_unit": 100})],
            }
        )
        move.action_post()
        self.env.flush_all()

        lines = self.env["sale.margin.report"].search([("invoice_id", "=", move.id)])
        self.assertTrue(lines)
        self.assertEqual(lines.manufacturer_id, manufacturer)

        groups = self.env["sale.margin.report"].formatted_read_group(
            [("invoice_id", "=", move.id)], ["manufacturer_id"], ["sale_val:sum"]
        )
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["manufacturer_id"][0], manufacturer.id)
        self.assertAlmostEqual(groups[0]["sale_val:sum"], 200)
