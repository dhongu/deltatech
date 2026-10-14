from odoo import Command, fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class TestProductInvoiceHistory(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a purchase journal
        self.purchase_journal = self.env["account.journal"].create(
            {
                "name": "Purchase Journal",
                "code": "PUR",
                "type": "purchase",
            }
        )

        # Create a sale journal
        self.sale_journal = self.env["account.journal"].create(
            {
                "name": "Sale Journal",
                "code": "SAL",
                "type": "sale",
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
        self.partner_a = self.env["res.partner"].create(
            {
                "name": "Testest partner",
            }
        )
        # Create invoices with line items
        self.invoice_in = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner_a.id,
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
                        },
                    )
                ],
            }
        )

        self.invoice_out = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
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


@tagged("post_install", "-at_install")
class TestProductInvoiceHistorySql(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_a = cls.env["product.product"].create({"name": "History product", "type": "consu"})
        cls.template = cls.product_a.product_tmpl_id
        cls.dozen = cls.env.ref("uom.product_uom_dozen")
        cls.partner = cls.env["res.partner"].create({"name": "History partner"})

    def _move(self, move_type, quantity, date=None, uom=None, post=True):
        date = date or fields.Date.today()
        line = {"product_id": self.product_a.id, "quantity": quantity, "price_unit": 10.0, "tax_ids": False}
        if uom:
            line["product_uom_id"] = uom.id
        move = self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner.id,
                "date": date,
                "invoice_date": date,
                "invoice_line_ids": [Command.create(line)],
            }
        )
        if post:
            move.action_post()
        return move

    def _history(self):
        self.template.refresh_invoice_history()
        return {
            rec.year: (rec.qty_in, rec.qty_out)
            for rec in self.env["product.invoice.history"].search([("template_id", "=", self.template.id)])
        }

    def test_customer_refund_is_subtracted(self):
        self._move("out_invoice", 10)
        self._move("out_refund", 2)
        year = str(fields.Date.today().year)
        self.assertEqual(self._history(), {year: (0.0, 8.0)})

    def test_vendor_refund_is_subtracted(self):
        self._move("in_invoice", 10)
        self._move("in_refund", 3)
        year = str(fields.Date.today().year)
        self.assertEqual(self._history(), {year: (7.0, 0.0)})

    def test_refund_equal_to_invoice_nets_to_zero(self):
        self._move("out_invoice", 4)
        self._move("out_refund", 4)
        year = str(fields.Date.today().year)
        self.assertEqual(self._history(), {year: (0.0, 0.0)})

    def test_draft_documents_are_ignored(self):
        self._move("out_invoice", 10)
        self._move("out_invoice", 5, post=False)
        year = str(fields.Date.today().year)
        self.assertEqual(self._history(), {year: (0.0, 10.0)})

    def test_quantity_converted_to_product_unit_and_split_by_year(self):
        today = fields.Date.today()
        self._move("out_invoice", 1, uom=self.dozen)
        self._move("out_refund", 2, uom=self.env.ref("uom.product_uom_unit"))
        self._move("out_invoice", 3, date=today.replace(year=today.year - 1))
        self.assertEqual(
            self._history(),
            {str(today.year): (0.0, 10.0), str(today.year - 1): (0.0, 3.0)},
        )

    def test_sql_matches_orm_computation(self):
        self._move("out_invoice", 10)
        self._move("out_refund", 2)
        self._move("in_invoice", 7)
        self._move("in_refund", 1)
        year = str(fields.Date.today().year)
        sql_history = self._history()
        self.template.invoice_history.unlink()
        self.template._compute_invoice_history()
        orm_history = {rec.year: (rec.qty_in, rec.qty_out) for rec in self.template.invoice_history}
        self.assertEqual(sql_history[year], (6.0, 8.0))
        self.assertEqual(orm_history[year], sql_history[year])

    def test_cron_refresh_for_all_products_matches_per_product_refresh(self):
        self._move("out_invoice", 10)
        self._move("out_refund", 2)
        self.env["product.template"]._cron_invoice_history()
        year = str(fields.Date.today().year)
        history = self.env["product.invoice.history"].search([("template_id", "=", self.template.id)])
        self.assertEqual([(rec.year, rec.qty_in, rec.qty_out) for rec in history], [(year, 0.0, 8.0)])
