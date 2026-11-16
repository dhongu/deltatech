# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

import unittest

from odoo.tests import TransactionCase, tagged
from odoo.tools.binary import BinaryBytes


def _has_renderpm_backend():
    """The picking operations report renders a barcode with reportlab renderPM, which needs
    the rlPyCairo or _rl_renderPM backend. Not every test image ships it."""
    for module in ("rlPyCairo", "_rl_renderPM"):
        try:
            __import__(module)
        except ImportError:
            continue
        return True
    return False


skip_without_renderpm = unittest.skipUnless(
    _has_renderpm_backend(), "reportlab renderPM backend (rlPyCairo/_rl_renderPM) is not installed"
)

# 1x1 PNG
PNG = BinaryBytes(
    bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000d49444154789c6360f8cfc000000301010018dd8db00000000049454e44ae426082"
    )
)


@tagged("post_install", "-at_install")
class TestPickingImage(TransactionCase):
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

    @skip_without_renderpm
    def test_picking_operations_image(self):
        self.picking.action_confirm()
        self.picking.move_ids.quantity = 2
        self.assertIn('alt="Image"', self._render("stock.action_report_picking"))

    def test_hide_on_pdf(self):
        self.env.company.hide_picking_image_pdf = True
        self.assertNotIn('alt="Image"', self._render("stock.action_report_delivery"))

    @skip_without_renderpm
    def test_hide_on_pdf_picking_operations(self):
        self.env.company.hide_picking_image_pdf = True
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
