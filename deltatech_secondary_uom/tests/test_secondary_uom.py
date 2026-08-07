# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSecondaryUom(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_kg = cls.env.ref("uom.product_uom_kgm")
        cls.uom_m2 = cls.env.ref("uom.product_uom_square_meter")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Tile",
                "type": "consu",
                "is_storable": True,
                "uom_id": cls.uom_unit.id,
                "secondary_uom_ids": [
                    # 3 m2 = 4 pieces -> one piece covers 0.75 m2
                    (0, 0, {"uom_id": cls.uom_m2.id, "uom_qty": 3.0, "base_qty": 4.0}),
                    # 1 kg = 2 pieces -> one piece weighs 0.5 kg
                    (0, 0, {"uom_id": cls.uom_kg.id, "uom_qty": 1.0, "base_qty": 2.0}),
                ],
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

    def test_conversion_helpers(self):
        conv_m2 = self.product.product_tmpl_id._get_secondary_uom_conversion(self.uom_m2)
        self.assertEqual(conv_m2._to_base_qty(3.0), 4.0)
        self.assertEqual(conv_m2._from_base_qty(4.0), 3.0)
        conv_kg = self.product.product_tmpl_id._get_secondary_uom_conversion(self.uom_kg)
        self.assertEqual(conv_kg._to_base_qty(10.0), 20.0)

    def test_conversion_constraints(self):
        with self.assertRaises(ValidationError):
            self.env["deltatech.product.uom.conversion"].create(
                {
                    "product_tmpl_id": self.product.product_tmpl_id.id,
                    "uom_id": self.uom_unit.id,  # same as base uom
                    "uom_qty": 1.0,
                    "base_qty": 1.0,
                }
            )
        with self.assertRaises(ValidationError):
            self.env["deltatech.product.uom.conversion"].create(
                {
                    "product_tmpl_id": self.product.product_tmpl_id.id,
                    "uom_id": self.env.ref("uom.product_uom_litre").id,
                    "uom_qty": 0.0,
                    "base_qty": 1.0,
                }
            )

    def test_sale_order_line_secondary_qty(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line:
            line.product_id = self.product
            line.secondary_uom_id = self.uom_m2
            line.secondary_uom_qty = 30.0  # 30 m2 -> 40 pieces
        order = order_form.save()
        self.assertEqual(order.order_line.product_uom_qty, 40.0)

        # editing the line quantity updates the secondary quantity
        with Form(order) as order_form:
            with order_form.order_line.edit(0) as line:
                line.product_uom_qty = 20.0  # 20 pieces -> 15 m2
        self.assertEqual(order.order_line.secondary_uom_qty, 15.0)

    def test_round_up_to_whole_pieces(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line:
            line.product_id = self.product
            line.secondary_uom_id = self.uom_m2
            line.secondary_uom_qty = 40.0  # 40 m2 -> 53.33 pieces -> rounded up to 54
        order = order_form.save()
        self.assertEqual(order.order_line.product_uom_qty, 54.0)
        # the secondary quantity is recomputed from the rounded pieces
        self.assertEqual(order.order_line.secondary_uom_qty, 40.5)

    def test_propagation_so_to_picking(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 40.0,
                            "secondary_uom_id": self.uom_m2.id,
                        },
                    )
                ],
            }
        )
        order.action_confirm()
        move = order.picking_ids.move_ids
        self.assertEqual(move.secondary_uom_id, self.uom_m2)
        self.assertEqual(move.secondary_uom_qty, 30.0)  # 40 pieces -> 30 m2

    def test_propagation_po_to_picking(self):
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 20.0,
                            "secondary_uom_id": self.uom_kg.id,
                        },
                    )
                ],
            }
        )
        order.button_confirm()
        move = order.picking_ids.move_ids
        self.assertEqual(move.secondary_uom_id, self.uom_kg)
        self.assertEqual(move.secondary_uom_qty, 10.0)  # 20 pieces -> 10 kg

    def test_purchase_order_line_secondary_qty(self):
        order_form = Form(self.env["purchase.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line:
            line.product_id = self.product
            line.secondary_uom_id = self.uom_kg
            line.secondary_uom_qty = 10.0  # 10 kg -> 20 pieces
        order = order_form.save()
        self.assertEqual(order.order_line.product_qty, 20.0)

    def test_stock_move_secondary_qty(self):
        picking_type = self.env.ref("stock.picking_type_in")
        move = self.env["stock.move"].create(
            {
                "product_id": self.product.id,
                "product_uom": self.uom_unit.id,
                "product_uom_qty": 1.0,
                "location_id": picking_type.default_location_src_id.id
                or self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": picking_type.default_location_dest_id.id,
                "picking_type_id": picking_type.id,
                "secondary_uom_id": self.uom_m2.id,
            }
        )
        move.secondary_uom_qty = 7.5  # 7.5 m2 -> 10 pieces
        self.assertEqual(move.product_uom_qty, 10.0)
