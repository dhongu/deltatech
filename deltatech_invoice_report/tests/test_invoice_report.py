from odoo import fields
from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestProductInvoiceHistory(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

    def setUp(self):
        super().setUp()

        # Create a purchase journal
        self.purchase_journal = self.env["account.journal"].create(
            {
                "name": "Purchase Journal",
                "code": "PUR",
                "type": "purchase",
                "default_account_id": self.company_data["default_account_expense"].id,
            }
        )

        # Create a sale journal
        self.sale_journal = self.env["account.journal"].create(
            {
                "name": "Sale Journal",
                "code": "SAL",
                "type": "sale",
                "default_account_id": self.company_data["default_account_revenue"].id,
            }
        )
        # Create a company
        self.company_test = self.env["res.company"].create(
            {
                "name": "Test Company",
            }
        )

        # Create a product category
        self.product_category = self.env["product.category"].create(
            {
                "name": "Test Category",
            }
        )

        # Create products and product templates
        self.product_template = self.env["product.template"].create(
            {
                "name": "Test Product Template",
                "categ_id": self.product_category.id,
            }
        )

        self.product = self.env["product.product"].create(
            {
                "product_tmpl_id": self.product_template.id,
            }
        )

        # Create invoices with line items
        self.invoice_in = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.env.ref("base.res_partner_1").id,
                "date": fields.Date.today(),
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 10,
                            "price_unit": 100,
                            "display_type": "product",
                        },
                    )
                ],
            }
        )

        self.invoice_out = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.env.ref("base.res_partner_1").id,
                "date": fields.Date.today(),
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 5,
                            "price_unit": 150,
                            "display_type": "product",
                        },
                    )
                ],
            }
        )

        # Post invoices to create journal entries
        self.invoice_in.action_post()
        self.invoice_out.action_post()

    def test_compute_invoice_history(self):
        # Compute invoice history
        self.product_template._compute_invoice_history()
        history_records = self.env["product.invoice.history"].search([("template_id", "=", self.product_template.id)])

        self.assertEqual(len(history_records), 1)
        history_record = history_records[0]
        self.assertEqual(history_record.year, str(fields.Date.today().year))
        self.assertEqual(history_record.qty_in, 10.0)
        self.assertEqual(history_record.qty_out, 5.0)

    def test_action_view_invoice_template(self):
        # Test action_view_invoice method on product template
        action = self.product_template.action_view_invoice()
        self.assertEqual(
            action["domain"],
            [
                ("move_type", "in", ["out_invoice", "out_refund"]),
                ("product_id", "in", self.product_template.product_variant_ids.ids),
            ],
        )
        self.assertIn("context", action)
        self.assertIn("group_by", action["context"])
        self.assertIn("measures", action["context"])

    def test_action_view_invoice_product(self):
        # Test action_view_invoice method on product product
        action = self.product.action_view_invoice()
        self.assertEqual(
            action["domain"],
            [("move_type", "in", ["out_invoice", "out_refund"]), ("product_id", "in", self.product.ids)],
        )
        self.assertIn("context", action)
        self.assertIn("group_by", action["context"])
        self.assertIn("measures", action["context"])
