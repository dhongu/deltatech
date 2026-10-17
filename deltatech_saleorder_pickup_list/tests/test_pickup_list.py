# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

import base64

from odoo.tests import TransactionCase, tagged
from odoo.tools import BinaryBytes

# 1x1 transparent PNG
PNG_1PX = BinaryBytes(
    base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
)


@tagged("post_install", "-at_install")
class TestSaleOrderPickupList(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids += cls.env.ref("uom.group_uom")
        cls.partner = cls.env["res.partner"].create({"name": "Pickup Customer"})
        cls.shipping = cls.env["res.partner"].create(
            {"name": "Pickup Shipping", "parent_id": cls.partner.id, "type": "delivery"}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Pickup Product",
                "type": "consu",
                "is_storable": True,
                "image_1920": PNG_1PX,
            }
        )
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.env["product.warehouse.location"].create(
            {
                "product_id": cls.product.product_tmpl_id.id,
                "warehouse_id": cls.warehouse.id,
                "loc_rack": "RK-7",
                "loc_row": "RW-3",
                "loc_case": "CS-9",
            }
        )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "partner_shipping_id": cls.shipping.id,
                "client_order_ref": "REF-PICK",
                "warehouse_id": cls.warehouse.id,
                "order_line": [
                    (0, 0, {"display_type": "line_section", "name": "Section A"}),
                    (0, 0, {"product_id": cls.product.id, "product_uom_qty": 4}),
                    (0, 0, {"display_type": "line_note", "name": "Handle with care"}),
                ],
            }
        )
        cls.report = cls.env.ref("deltatech_saleorder_pickup_list.action_report_saleorder_pickup_list")

    def _render(self):
        html, report_type = self.env["ir.actions.report"]._render_qweb_html(self.report, self.order.ids)
        self.assertEqual(report_type, "html")
        return html.decode() if isinstance(html, bytes) else str(html)

    def test_report_action(self):
        self.assertEqual(self.report.model, "sale.order")
        self.assertEqual(self.report.binding_model_id.model, "sale.order")

    def test_render_pickup_list(self):
        html = self._render()
        for text in (
            self.order.name,
            "REF-PICK",
            "Pickup Product",
            "RK-7",
            "RW-3",
            "CS-9",
            "Section A",
            "Handle with care",
            "Pickup Shipping",
            "data:image/png;base64,",
        ):
            self.assertIn(text, html)

    def test_render_confirmed_order(self):
        self.order.action_confirm()
        html = self._render()
        self.assertIn("Order #", html)
        self.assertIn(self.order.name, html)
