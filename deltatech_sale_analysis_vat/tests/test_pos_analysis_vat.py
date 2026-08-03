# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged("post_install", "-at_install")
class TestPosAnalysisVat(TestPoSCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.basic_config
        cls.tax_vat = cls.env["account.tax"].create(
            {
                "name": "VAT 21%",
                "amount_type": "percent",
                "amount": 21.0,
                "type_tax_use": "sale",
                "sequence": 10,
                "company_id": cls.env.company.id,
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
                "company_id": cls.env.company.id,
            }
        )
        cls.product_vat = cls.create_product(
            "Product with VAT", cls.categ_basic, 100.0, tax_ids=(cls.tax_fixed | cls.tax_vat).ids
        )

    def test_vat_dimension_on_pos_report(self):
        self.open_new_session()
        # An order is only invoiced once it is paid, so the payment has to be part of the
        # order data - the total is taken from the order data itself.
        invoiced_args = {
            "pos_order_lines_ui_args": [(self.product_vat, 2)],
            "customer": self.partner_a,
            "is_invoiced": True,
            "uuid": "receipt-invoiced",
        }
        total = self.create_ui_order_data(**invoiced_args)["amount_total"]
        invoiced_args["payments"] = [(self.cash_pm1, total)]
        orders = self._create_orders(
            [
                {"pos_order_lines_ui_args": [(self.product_vat, 1)], "uuid": "receipt-only"},
                invoiced_args,
            ]
        )
        # The reports are SQL views, so pending ORM values have to reach the database first.
        self.env.flush_all()
        report = self.env["report.pos.order"]

        plain = report.search([("order_id", "=", orders["receipt-only"].id)])
        self.assertEqual(len(plain), 1, "One report line per order line")
        self.assertEqual(plain.vat_tax_id, self.tax_vat, "The percentage tax must be reported as VAT")
        self.assertEqual(plain.vat_tax_group_id, self.tax_vat.tax_group_id)
        self.assertFalse(plain.invoiced)

        invoiced = report.search([("order_id", "=", orders["receipt-invoiced"].id)])
        self.assertEqual(len(invoiced), 1)
        self.assertEqual(invoiced.vat_tax_id, self.tax_vat)
        self.assertTrue(invoiced.invoiced, "The receipt is flagged as invoiced, so it can be filtered out")

        # The same turnover must not be reported twice: the invoice issued for a fiscal
        # receipt is flagged, so it can be excluded from the invoice analysis.
        invoice_report = self.env["account.invoice.report"].search(
            [("move_id", "=", orders["receipt-invoiced"].account_move.id)]
        )
        self.assertTrue(invoice_report.is_fiscal_receipt)
        self.assertEqual(invoice_report.vat_tax_id, self.tax_vat)
