# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestMRPSimple(TransactionCase):
    def setUp(self):
        super(TestMRPSimple, self).setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"partner_id": self.partner_a.id})]
        self.product_a = self.env["product.product"].create(
            {"name": "Test A", "type": "product", "standard_price": 100, "list_price": 150, "seller_ids": seller_ids}
        )
        self.product_b = self.env["product.product"].create(
            {"name": "Test B", "type": "product", "standard_price": 70, "list_price": 150, "seller_ids": seller_ids}
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

        warehouse_id = self.stock_location.get_warehouse()
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
        mrp.final_product_name = "Test Finish Product"
        mrp.final_product_category = self.env.ref("product.product_category_all")
        mrp.final_product_uom_id = self.env.ref("uom.product_uom_unit")
        mrp.partner_id = self.partner
        mrp.auto_create_sale = True
        mrp = mrp.save()

        mrp.create_final_product()
        mrp.do_transfer()

        mrp.create_sale()
        mrp.sale_order_id.action_confirm()
        mrp.sale_order_id.action_view_mrp()
