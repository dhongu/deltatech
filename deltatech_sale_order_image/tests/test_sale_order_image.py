# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged
from odoo.tools.binary import BinaryBytes

# 1x1 PNG
PNG = BinaryBytes(
    bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000d49444154789c6360f8cfc000000301010018dd8db00000000049454e44ae426082"
    )
)


@tagged("post_install", "-at_install")
class TestSaleOrderImage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create({"name": "Image product", "image_1920": PNG})
        cls.so = cls.env["sale.order"].create(
            {
                "partner_id": cls.env["res.partner"].create({"name": "Customer"}).id,
                "order_line": [
                    (0, 0, {"display_type": "line_section", "name": "Section"}),
                    (0, 0, {"product_id": cls.product.id, "product_uom_qty": 1}),
                ],
            }
        )

    def _render(self):
        action = self.env.ref("sale.action_report_saleorder")
        html, _ = self.env["ir.actions.report"]._render_qweb_html(action, self.so.ids)
        return html.decode()

    def test_default_enabled(self):
        self.assertTrue(self.env.company.include_image_line)

    def test_image_rendered_when_enabled(self):
        self.env.company.include_image_line = True
        html = self._render()
        self.assertIn("data:image/", html)
        self.assertIn('alt="Image"', html)

    def test_image_hidden_when_disabled(self):
        self.env.company.include_image_line = False
        html = self._render()
        self.assertNotIn('alt="Image"', html)
