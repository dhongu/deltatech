from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestDocumentWeight(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create({"name": "Weight Partner", "lang": "en_US"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Weighted product",
                "weight": 2.0,
                "volume": 0.5,
                "l10n_ro_net_weight": 1.5,
                "list_price": 10.0,
            }
        )
        cls.light = cls.env["product.product"].create({"name": "No weight product", "list_price": 5.0})
        cls.dozen = cls.env.ref("uom.product_uom_dozen")

    def _order(self, lines=None):
        lines = lines or [(self.product, 3.0, None)]
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_qty": qty,
                            **({"product_uom_id": uom.id} if uom else {}),
                        },
                    )
                    for product, qty, uom in lines
                ],
            }
        )

    def _invoice(self, qty=3.0):
        return self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [(0, 0, {"product_id": self.product.id, "quantity": qty, "price_unit": 10.0})],
            }
        )

    def _html(self, report_ref, record):
        html, _report_type = self.env["ir.actions.report"]._render_qweb_html(report_ref, record.ids)
        # the decimal separator follows the language of the database: compare with a dot
        return html.decode().replace(",", ".")

    def test_line_weights_in_product_uom(self):
        self.assertEqual(
            self.product._get_document_weights(3.0),
            {"net": 4.5, "gross": 6.0, "volume": 1.5},
        )

    def test_line_weights_convert_the_line_uom(self):
        # 2 dozens = 24 units: the weights are those of the product unit, not of the dozen
        weights = self.product._get_document_weights(2.0, self.dozen)
        self.assertAlmostEqual(weights["net"], 36.0)
        self.assertAlmostEqual(weights["gross"], 48.0)
        self.assertAlmostEqual(weights["volume"], 12.0)

    def test_sale_order_totals_skip_sections_and_notes(self):
        order = self._order([(self.product, 3.0, None), (self.light, 4.0, None)])
        self.env["sale.order.line"].create({"order_id": order.id, "display_type": "line_section", "name": "Section"})
        totals = order._get_document_weight_totals()
        self.assertEqual(totals, {"net": 4.5, "gross": 6.0, "volume": 1.5})

    def test_invoice_totals(self):
        totals = self._invoice(qty=2.0)._get_document_weight_totals()
        self.assertEqual(totals, {"net": 3.0, "gross": 4.0, "volume": 1.0})

    def test_labels_follow_the_database_units(self):
        labels = self.env["sale.order"]._get_document_weight_labels()
        template = self.env["product.template"]
        self.assertEqual(labels["weight"], template._get_weight_uom_name_from_ir_config_parameter())
        self.assertEqual(labels["volume"], template._get_volume_uom_name_from_ir_config_parameter())

    def test_quotation_report_on_by_default(self):
        self.assertTrue(self.company.document_weight_on_sale)
        html = self._html("sale.action_report_saleorder", self._order())
        self.assertIn("Net weight:", html)
        self.assertIn("Total gross weight:", html)
        self.assertIn("6.00", html)

    def test_quotation_report_off(self):
        self.company.document_weight_on_sale = False
        html = self._html("sale.action_report_saleorder", self._order())
        self.assertNotIn("Net weight:", html)
        self.assertNotIn("Total net weight:", html)

    def test_quotation_report_hides_the_block_without_weights(self):
        html = self._html("sale.action_report_saleorder", self._order([(self.light, 1.0, None)]))
        self.assertNotIn("Net weight:", html)
        self.assertNotIn("Total net weight:", html)

    def test_invoice_report_off_by_default(self):
        self.assertFalse(self.company.document_weight_on_invoice)
        html = self._html("account.account_invoices", self._invoice())
        self.assertNotIn("Net weight:", html)
        self.assertNotIn("Total net weight:", html)

    def test_invoice_report_on(self):
        self.company.document_weight_on_invoice = True
        html = self._html("account.account_invoices", self._invoice())
        self.assertIn("Net weight:", html)
        self.assertIn("Total net weight:", html)
        self.assertIn("4.50", html)

    def test_settings_write_the_company_flags(self):
        with Form(self.env["res.config.settings"]) as form:
            form.document_weight_on_invoice = True
            form.document_weight_on_sale = False
        settings = form.save()
        settings.execute()
        self.assertTrue(self.company.document_weight_on_invoice)
        self.assertFalse(self.company.document_weight_on_sale)
