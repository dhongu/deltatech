# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

import base64

from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon

# 1x1 PNG
PNG = base64.b64encode(
    bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000d49444154789c6360f8cfc000000301010018dd8db00000000049454e44ae426082"
    )
)


@tagged("post_install", "-at_install")
class TestPickingImage(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Image product", "is_storable": True, "image_1920": PNG}
        )
        cls.picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 2,
                            "location_id": cls.env.ref("stock.stock_location_stock").id,
                            "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                        },
                    )
                ],
            }
        )

    def _render(self, xmlid):
        html, _ = self.env["ir.actions.report"]._render_qweb_html(xmlid, self.picking.ids)
        return html.decode()

    def test_move_image_related(self):
        self.assertEqual(self.picking.move_ids.product_image, self.product.image_128)

    def test_delivery_slip_image(self):
        self.assertIn('alt="Image"', self._render("stock.action_report_delivery"))

    def test_picking_operations_image(self):
        self.picking.action_confirm()
        self.picking.move_ids.quantity = 2
        self.assertIn('alt="Image"', self._render("stock.action_report_picking"))

    def test_hide_on_pdf(self):
        self.env.company.hide_picking_image_pdf = True
        self.assertNotIn('alt="Image"', self._render("stock.action_report_delivery"))
        self.picking.action_confirm()
        self.picking.move_ids.quantity = 2
        self.assertNotIn('alt="Image"', self._render("stock.action_report_picking"))

    def test_delivery_slip_done_image(self):
        self.picking.action_confirm()
        self.picking.move_ids.quantity = 2
        self.picking.move_ids.picked = True
        self.picking.button_validate()
        self.assertEqual(self.picking.state, "done")
        self.assertIn('alt="Image"', self._render("stock.action_report_delivery"))
