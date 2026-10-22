# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestInvoiceReportManufacturer(AccountTestInvoicingCommon):
    def test_manufacturer_in_invoice_report(self):
        manufacturer = self.env["res.partner"].create({"name": "Manufacturer TEST", "is_manufacturer": True})
        self.product_a.manufacturer_id = manufacturer
        move = self.init_invoice("out_invoice", products=self.product_a, post=True)
        self.env.flush_all()

        lines = self.env["account.invoice.report"].search([("move_id", "=", move.id)])
        self.assertTrue(lines)
        self.assertEqual(lines.manufacturer_id, manufacturer)
