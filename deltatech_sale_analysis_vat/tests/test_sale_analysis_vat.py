# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestSaleAnalysisVat(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tax_vat = cls.env["account.tax"].create(
            {
                "name": "VAT 21%",
                "amount_type": "percent",
                "amount": 21.0,
                "type_tax_use": "sale",
                "sequence": 10,
                "company_id": cls.company_data["company"].id,
            }
        )
        # A fixed tax such as the green tax must never be picked up as the VAT rate.
        cls.tax_fixed = cls.env["account.tax"].create(
            {
                "name": "Green tax",
                "amount_type": "fixed",
                "amount": 3.5,
                "type_tax_use": "sale",
                "sequence": 1,
                "company_id": cls.company_data["company"].id,
            }
        )
        # A product without cost, so that modules refusing to sell below the purchase
        # price do not interfere with the invoices created here.
        cls.product_vat = cls.env["product.product"].create(
            {
                "name": "Product for VAT analysis",
                "is_storable": True,
                "lst_price": 100.0,
                "standard_price": 0.0,
            }
        )

    def _create_invoice(self, taxes):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": "2026-07-15",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_vat.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, taxes.ids)],
                        },
                    )
                ],
            }
        )
        invoice.action_post()
        return invoice

    def test_vat_dimension_on_invoice_report(self):
        invoice = self._create_invoice(self.tax_fixed | self.tax_vat)
        report = self.env["account.invoice.report"].search([("move_id", "=", invoice.id)])
        self.assertEqual(len(report), 1)
        self.assertEqual(report.vat_tax_id, self.tax_vat, "The percentage tax must be reported as VAT")
        self.assertEqual(report.vat_tax_group_id, self.tax_vat.tax_group_id)
        self.assertFalse(report.is_fiscal_receipt, "A plain invoice is not issued for a fiscal receipt")

    def test_invoice_without_tax(self):
        invoice = self._create_invoice(self.env["account.tax"])
        report = self.env["account.invoice.report"].search([("move_id", "=", invoice.id)])
        self.assertEqual(len(report), 1, "A line without taxes must still be reported once")
        self.assertFalse(report.vat_tax_id)

    def test_line_is_not_duplicated_by_several_taxes(self):
        tax_second_vat = self.tax_vat.copy({"name": "VAT 11%", "amount": 11.0, "sequence": 20})
        invoice = self._create_invoice(self.tax_vat | tax_second_vat)
        report = self.env["account.invoice.report"].search([("move_id", "=", invoice.id)])
        self.assertEqual(len(report), 1, "A line with two VAT taxes must be reported once")
        self.assertEqual(report.vat_tax_id, self.tax_vat, "The tax with the lowest sequence wins")
