# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


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

    def _simple(self, received, consumed_value=100.0):
        """received: list of (product, quantity); one consumed line worth consumed_value"""
        return self.env["mrp.simple"].create(
            {
                "picking_type_consume": self.picking_type_consume.id,
                "picking_type_receipt_production": self.picking_type_receipt_production.id,
                "product_in_ids": [
                    (0, 0, {"product_id": product.id, "quantity": qty, "uom_id": product.uom_id.id})
                    for product, qty in received
                ],
                "product_out_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_b.id,
                            "quantity": 1,
                            "price_unit": consumed_value,
                            "uom_id": self.product_b.uom_id.id,
                        },
                    )
                ],
            }
        )

    def test_cost_split_over_several_received_products(self):
        """SIMPLE-001: the consumed cost is allocated once, not to every received product"""
        mrp = self._simple([(self.product_a, 2), (self.product_b, 3)])
        mrp.compute_finit_price()
        line_a, line_b = mrp.product_in_ids
        # prices are rounded to the "Product Price" precision
        self.assertAlmostEqual(sum(mrp.product_in_ids.mapped("value")), 100.0, delta=0.01)
        # standard values 2 x 100 = 200 and 3 x 70 = 210
        self.assertAlmostEqual(line_a.value, 100.0 * 200 / 410, delta=0.01)
        self.assertAlmostEqual(line_b.value, 100.0 * 210 / 410, delta=0.01)

    def test_cost_split_by_quantity_without_standard_price(self):
        product_c = self.env["product.product"].create({"name": "Test C", "is_storable": True})
        product_d = self.env["product.product"].create({"name": "Test D", "is_storable": True})
        mrp = self._simple([(product_c, 1), (product_d, 3), (self.product_a, 0)])
        mrp.compute_finit_price()
        line_c, line_d, line_zero = mrp.product_in_ids
        self.assertAlmostEqual(line_c.value, 25.0)
        self.assertAlmostEqual(line_d.value, 75.0)
        self.assertEqual(line_zero.price_unit, 0.0)

    def test_single_received_product_keeps_whole_cost(self):
        mrp = self._simple([(self.product_a, 4)])
        mrp.compute_finit_price()
        self.assertAlmostEqual(mrp.product_in_ids.price_unit, 25.0)

    def test_confirm_only_once(self):
        """SIMPLE-002: a second confirmation does not move the stock again"""
        mrp = self._simple([(self.product_a, 2)])
        mrp.compute_finit_price()
        mrp.do_transfer()
        self.assertEqual(mrp.state, "done")
        consume, receipt = mrp.consume_id, mrp.receipt_id
        pickings = self.env["stock.picking"].search_count([])
        with self.assertRaises(UserError):
            mrp.do_transfer()
        self.assertEqual(self.env["stock.picking"].search_count([]), pickings)
        self.assertEqual((mrp.consume_id, mrp.receipt_id), (consume, receipt))
