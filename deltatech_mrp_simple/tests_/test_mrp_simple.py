# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests.common import TransactionCase


class TestMRPSimple(TransactionCase):
    def setUp(self):
        super(TestMRPSimple, self).setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test"})

        seller_ids = [(0, 0, {"name": self.partner_a.id})]
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
        product_in = {
            "product_id": self.product_a.id,
            "quantity": 2,
            "price_unit": self.product_a.standard_price,
            "uom_id": self.product_a.uom_id.id,
        }
        product_out = {
            "product_id": self.product_b.id,
            "quantity": 1,
            "price_unit": self.product_b.standard_price,
            "uom_id": self.product_b.uom_id.id,
        }
        mrp = self.env["mrp.simple"].create(
            {
                "picking_type_consume": self.picking_type_consume.id,
                "picking_type_receipt_production": self.picking_type_receipt_production.id,
                "product_in_ids": [(0, 0, product_in)],
                "product_out_ids": [(0, 0, product_out)],
                "validation_consume": True,
            }
        )

        mrp.do_transfer()
