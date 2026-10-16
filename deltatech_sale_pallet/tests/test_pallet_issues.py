# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPalletIssues(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Pallet"})
        cls.pallet = cls.env["product.product"].create({"name": "Pallet", "type": "consu", "list_price": 20})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Bricks",
                "type": "consu",
                "list_price": 5,
                "pallet_product_id": cls.pallet.id,
                "pallet_qty_min": 10,
            }
        )

    def test_onchange_registered_under_own_name(self):
        # PALLET-002 (#3463): a generic `onchange_order_line` is overridden without
        # super() by other addons (deltatech_sale_add_extra_line), so only one runs.
        names = [
            getattr(method, "__name__", "") for method in self.env["sale.order"]._onchange_methods.get("order_line", [])
        ]
        self.assertIn("_onchange_order_line_pallet", names)

    def test_pallet_line_removed_with_last_main_product(self):
        # PALLET-003 (#3464)
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line:
            line.product_id = self.product
            line.product_uom_qty = 20
        pallet_lines = [
            i for i in range(len(order_form.order_line)) if order_form.order_line.edit(i).product_id == self.pallet
        ]
        self.assertEqual(len(pallet_lines), 1)
        self.assertEqual(order_form.order_line.edit(pallet_lines[0]).product_uom_qty, 2)

        main_index = next(
            i for i in range(len(order_form.order_line)) if order_form.order_line.edit(i).product_id == self.product
        )
        order_form.order_line.remove(main_index)
        order = order_form.save()
        self.assertFalse(order.order_line.filtered(lambda sol: sol.product_id == self.pallet))

    def test_manual_pallet_line_kept(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line:
            line.product_id = self.pallet
            line.product_uom_qty = 3
        order = order_form.save()
        self.assertEqual(order.order_line.product_id, self.pallet)
        self.assertEqual(order.order_line.product_uom_qty, 3)

    def test_pallet_price_dependencies(self):
        # PALLET-004 (#3465)
        template = self.product.product_tmpl_id
        self.assertEqual(template.pallet_price, 20 + 10 * 5)
        self.pallet.list_price = 30
        self.assertEqual(template.pallet_price, 30 + 10 * 5)
        template.list_price = 6
        self.assertEqual(template.pallet_price, 30 + 10 * 6)
        template.pallet_qty_min = 5
        self.assertEqual(template.pallet_price, 30 + 5 * 6)
