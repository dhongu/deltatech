# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestWarranty(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Warranty Customer"})
        cls.product_warranty = cls.env["product.product"].create(
            {"name": "Laptop With Warranty", "type": "consu", "list_price": 100, "warranty_months": 24}
        )
        cls.product_plain = cls.env["product.product"].create(
            {"name": "Cable Without Warranty", "type": "consu", "list_price": 5}
        )

    def _create_order(self, products):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": product.id, "product_uom_qty": 1}) for product in products],
            }
        )

    def _render(self, order):
        html, _ = self.env["ir.actions.report"]._render_qweb_html("sale.action_report_saleorder", order.ids)
        return html.decode()

    def test_warranty_field(self):
        self.assertEqual(self.product_warranty.product_tmpl_id.warranty_months, 24)
        self.assertEqual(self.product_plain.warranty_months, 0)

    def test_report_with_warranty_page(self):
        order = self._create_order(self.product_warranty | self.product_plain)
        html = self._render(order)
        self.assertIn('id="warranty_content"', html)
        self.assertIn("Laptop With Warranty", html)
        warranty_part = html.split('id="warranty_content"', 1)[1]
        self.assertIn("Laptop With Warranty", warranty_part)
        self.assertIn("24", warranty_part)
        self.assertNotIn("Cable Without Warranty", warranty_part)

    def test_report_without_warranty_page(self):
        order = self._create_order(self.product_plain)
        html = self._render(order)
        self.assertNotIn('id="warranty_content"', html)
