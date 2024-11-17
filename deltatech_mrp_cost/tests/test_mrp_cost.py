# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import fields
from odoo.tests import Form

from odoo.addons.mrp.tests.common import TestMrpCommon


class TestMrpOrder(TestMrpCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref("base.group_user").write({"implied_ids": [(4, cls.env.ref("stock.group_production_lot").id)]})

    def test_basic(self):
        """Checks a basic manufacturing order: no routing (thus no workorders), no lot and
        consume strictly what's needed."""
        self.product_1.is_storable = True
        self.product_2.is_storable = True
        self.env["stock.quant"].create(
            {
                "location_id": self.warehouse_1.lot_stock_id.id,
                "product_id": self.product_1.id,
                "inventory_quantity": 500,
            }
        ).action_apply_inventory()
        self.env["stock.quant"].create(
            {
                "location_id": self.warehouse_1.lot_stock_id.id,
                "product_id": self.product_2.id,
                "inventory_quantity": 500,
            }
        ).action_apply_inventory()

        test_date_planned = fields.Datetime.now() - timedelta(days=1)
        test_quantity = 3.0
        man_order_form = Form(self.env["mrp.production"].with_user(self.user_mrp_user))
        man_order_form.product_id = self.product_4
        man_order_form.bom_id = self.bom_1
        man_order_form.product_uom_id = self.product_4.uom_id
        man_order_form.product_qty = test_quantity
        man_order_form.date_start = test_date_planned
        man_order_form.location_src_id = self.location_1
        man_order_form.location_dest_id = self.warehouse_1.wh_output_stock_loc_id
        man_order = man_order_form.save()

        man_order.action_confirm()
