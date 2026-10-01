# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestMRPSimple(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"partner_id": self.partner_a.id})]
        self.product_a = self.env["product.product"].create(
            {
                "name": "Test A",
                "type": "consu",
                "is_storable": True,
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        self.product_b = self.env["product.product"].create(
            {
                "name": "Test B",
                "type": "consu",
                "is_storable": True,
                "standard_price": 70,
                "list_price": 150,
                "seller_ids": seller_ids,
            }
        )
        self.stock_location = self.env.ref("stock.stock_location_stock")
        # inv_line_a = {
        #     "product_id": self.product_a.id,
        #     "product_qty": 10000,
        #     "location_id": self.stock_location.id,
        # }
        # inv_line_b = {
        #     "product_id": self.product_b.id,
        #     "product_qty": 10000,
        #     "location_id": self.stock_location.id,
        # }

        warehouse_id = self.stock_location.warehouse_id
        company_id = warehouse_id.company_id
        domain = [("usage", "=", "production"), ("company_id", "=", company_id.id)]
        self.location_production = self.env["stock.location"].search(domain, limit=1)

        self.picking_type_consume = self.env["stock.picking.type"].create(
            {
                "name": "Consume",
                "code": "internal",
                "sequence_code": "__test_c__",
                "default_location_src_id": self.stock_location.id,
                "default_location_dest_id": self.location_production.id,
                "warehouse_id": warehouse_id.id,
                "company_id": company_id.id,
            }
        )

        self.picking_type_receipt_production = self.env["stock.picking.type"].create(
            {
                "name": "Production",
                "code": "internal",
                "sequence_code": "__test_p__",
                "default_location_src_id": self.location_production.id,
                "default_location_dest_id": self.stock_location.id,
                "warehouse_id": warehouse_id.id,
                "company_id": company_id.id,
            }
        )
        self.env["stock.quant"]._update_available_quantity(self.product_a, self.stock_location, 1000)
        self.env["stock.quant"]._update_available_quantity(self.product_b, self.stock_location, 1000)

        self.partner = self.env["res.partner"].create({"name": "Test"})

        # inventory = self.env["stock.inventory"].create(
        #     {
        #         "name": "Inv. product",
        #         "line_ids": [
        #             (0, 0, inv_line_a),
        #             (0, 0, inv_line_b),
        #         ],
        #     }
        # )
        # inventory.action_start()
        # inventory.action_validate()

    def test_sale_mrp_simple(self):
        mrp = Form(self.env["mrp.simple"])
        mrp.picking_type_consume = self.picking_type_consume
        mrp.picking_type_receipt_production = self.picking_type_receipt_production
        with mrp.product_in_ids.new() as line:
            line.product_id = self.product_a
            line.quantity = 2
            line.price_unit = self.product_a.standard_price
            line.uom_id = self.product_a.uom_id
        with mrp.product_out_ids.new() as line:
            line.product_id = self.product_b
            line.quantity = 1

        mrp.validation_consume = True
        mrp.auto_create_sale = True
        mrp.final_product_name = "Test Finish Product"
        mrp.final_product_category = self.env.ref("product.product_category_goods")
        mrp.final_product_uom_id = self.env.ref("uom.product_uom_unit")
        mrp.partner_id = self.partner

        mrp = mrp.save()

        mrp.create_final_product()
        mrp.do_transfer()

        mrp.create_sale()
        mrp.sale_order_id.action_confirm()
        mrp.sale_order_id.action_view_mrp()

    def _new_mrp(self, price_unit=100):
        mrp = Form(self.env["mrp.simple"])
        mrp.picking_type_consume = self.picking_type_consume
        mrp.picking_type_receipt_production = self.picking_type_receipt_production
        with mrp.product_in_ids.new() as line:
            line.product_id = self.product_a
            line.quantity = 2
            line.price_unit = price_unit
        with mrp.product_out_ids.new() as line:
            line.product_id = self.product_b
            line.quantity = 3
        return mrp.save()

    def test_mrp_simple_moves(self):
        mrp = self._new_mrp()
        mrp.validation_consume = True
        qty_a = self.product_a.qty_available
        qty_b = self.product_b.qty_available
        mrp.do_transfer()
        self.assertEqual(mrp.state, "done")
        self.assertEqual(mrp.consume_id.state, "done")
        self.assertEqual(mrp.receipt_id.state, "done")
        self.assertEqual(mrp.consume_id.move_ids.uom_id, self.product_b.uom_id)
        self.assertEqual(mrp.receipt_id.move_ids.uom_id, self.product_a.uom_id)
        self.assertEqual(self.product_a.qty_available, qty_a + 2)
        self.assertEqual(self.product_b.qty_available, qty_b - 3)
        self.assertEqual(mrp.open_consume()["res_id"], mrp.consume_id.id)
        self.assertEqual(mrp.open_receipt()["res_id"], mrp.receipt_id.id)

    def test_mrp_simple_zero_cost(self):
        mrp = self._new_mrp(price_unit=0)
        with self.assertRaises(UserError):
            mrp.do_transfer()
        self.env["ir.config_parameter"].sudo().set_bool("deltatech_mrp_simple.allow_zero_cost", True)
        mrp = self._new_mrp(price_unit=0)
        mrp.do_transfer()
        self.assertEqual(mrp.state, "done")

    def test_mrp_simple_recompute_price(self):
        mrp = self._new_mrp(price_unit=1)
        mrp.compute_finit_price()
        self.assertAlmostEqual(mrp.product_in_ids.price_unit, 3 * 70 / 2)

    def test_add_multi_lines(self):
        mrp = self._new_mrp()
        action = mrp.add_multiple_lines()
        wizard = self.env["add.multi.mrp.lines"].browse(action["res_id"])
        wizard.qty = 4
        wizard.product_lines = [Command.create({"product_ids": [Command.set(self.product_a.ids)]})]
        wizard.add_products()
        line = mrp.product_out_ids.filtered(lambda line: line.product_id == self.product_a)
        self.assertEqual(line.quantity, 4)
        self.assertEqual(line.price_unit, self.product_a.standard_price)

    def test_sale_existing_final_product(self):
        mrp = self._new_mrp()
        mrp.auto_create_sale = True
        mrp.partner_id = self.partner
        mrp.final_product_id = self.product_a
        mrp.final_product_name = "Custom description"
        mrp.final_product_qty = 1
        mrp.do_transfer()
        sale_line = mrp.sale_order_id.order_line
        self.assertEqual(sale_line.product_id, self.product_a)
        self.assertEqual(sale_line.name, "Custom description")
        self.assertEqual(mrp.sale_order_id.simple_mrp_count, 1)
