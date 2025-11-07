# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import Command, TransactionCase


@tagged("post_install", "-at_install")
class TestProcurementPerSalesTeam(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.company = env.company

        # Create a vendor
        cls.vendor = env["res.partner"].create(
            {
                "name": "Vendor A",
                "supplier_rank": 1,
                "company_id": cls.company.id,
            }
        )

        # Create product purchasable with Buy + MTO
        cls.product = env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
                "purchase_ok": True,
                "sale_ok": True,
                "uom_id": env.ref("uom.product_uom_unit").id,
                "uom_po_id": env.ref("uom.product_uom_unit").id,
            }
        )
        # Assign routes: Buy and MTO
        buy_route = env.ref("purchase_stock.route_warehouse0_buy")
        mto_route = env.ref("stock.route_warehouse0_mto")
        cls.product.write(
            {
                "route_ids": [
                    Command.link(buy_route.id),
                    Command.link(mto_route.id),
                ]
            }
        )
        # Create vendor seller on product
        env["product.supplierinfo"].create(
            {
                "partner_id": cls.vendor.id,
                "product_tmpl_id": cls.product.product_tmpl_id.id,
                "min_qty": 1.0,
                "price": 10.0,
            }
        )

        # Adjust the delivery rule "WH: Stock → Customers" to use MTS else MTO
        # so that the Buy rule will be triggered during procurement planning.
        warehouse = env["stock.warehouse"].search([("company_id", "=", cls.company.id)], limit=1)
        if not warehouse:
            warehouse = env.ref("stock.warehouse0", raise_if_not_found=False)
        if warehouse:
            delivery_rule = env["stock.rule"].search(
                [
                    ("location_src_id", "=", warehouse.lot_stock_id.id),
                    ("location_dest_id.usage", "=", "customer"),
                ],
                limit=1,
            )
            if delivery_rule:
                delivery_rule.write({"procure_method": "mts_else_mto"})

        # Create a reordering rule (min/max) for the product to ensure scheduler can plan purchases too
        # warehouse = env['stock.warehouse'].search([('company_id', '=', cls.company.id)], limit=1)
        # if not warehouse:
        #     warehouse = env.ref('stock.warehouse0', raise_if_not_found=False)
        # if warehouse:
        #     env['stock.warehouse.orderpoint'].create({
        #         'name': 'OP Test Product',
        #         'company_id': cls.company.id,
        #         'warehouse_id': warehouse.id,
        #         'location_id': warehouse.lot_stock_id.id,
        #         'product_id': cls.product.id,
        #         'product_min_qty': 0.0,
        #         'product_max_qty': 10.0,
        #         'qty_multiple': 1.0,
        #     })

        # Customers
        cls.customer = env["res.partner"].create(
            {
                "name": "Customer X",
                "customer_rank": 1,
                "company_id": cls.company.id,
            }
        )

        # Two sales teams
        cls.team_a = env["crm.team"].create({"name": "Team A"})
        cls.team_b = env["crm.team"].create({"name": "Team B"})

        # Pricelist mandatory for sales
        cls.pricelist = env["product.pricelist"].create(
            {
                "name": "Public",
                "currency_id": cls.company.currency_id.id,
            }
        )

        # Four sale orders: 2 per team
        def _make_so(team, name):
            so = env["sale.order"].create(
                {
                    "partner_id": cls.customer.id,
                    "team_id": team.id,
                    "pricelist_id": cls.pricelist.id,
                    "company_id": cls.company.id,
                    "origin": name,
                }
            )
            env["sale.order.line"].create(
                {
                    "order_id": so.id,
                    "product_id": cls.product.id,
                    "product_uom_qty": 2.0,
                }
            )
            return so

        cls.so_a1 = _make_so(cls.team_a, "SO A1")
        cls.so_a2 = _make_so(cls.team_a, "SO A2")
        cls.so_b1 = _make_so(cls.team_b, "SO B1")
        cls.so_b2 = _make_so(cls.team_b, "SO B2")

    def _confirm_and_run_procurements(self, *sos):
        # Confirm SOs to create procurements
        for so in sos:
            so.action_confirm()
        # In most flows, confirming SO triggers procurement directly.
        # Ensure any pending procurements are processed by running the scheduler minimal API.
        self.env["procurement.group"].run_scheduler()

    def test_purchase_orders_generated_per_sales_team(self):
        self._confirm_and_run_procurements(self.so_a1, self.so_a2, self.so_b1, self.so_b2)

        # Fetch POs for our vendor
        pos = self.env["purchase.order"].search(
            [
                ("partner_id", "=", self.vendor.id),
                ("state", "=", "draft"),
            ]
        )
        # Expect 2 POs: one for Team A and one for Team B
        self.assertEqual(len(pos), 2, "Expected exactly 2 draft POs (one per team)")

        po_team_a = pos.filtered(lambda p: p.team_id == self.team_a)
        po_team_b = pos.filtered(lambda p: p.team_id == self.team_b)
        self.assertEqual(len(po_team_a), 1, "Expected one PO for Team A")
        self.assertEqual(len(po_team_b), 1, "Expected one PO for Team B")

        # Quantities: each SO ordered 2 units, 2 SOs per team => 4 units per PO
        self.assertAlmostEqual(sum(po_team_a.order_line.mapped("product_qty")), 4.0)
        self.assertAlmostEqual(sum(po_team_b.order_line.mapped("product_qty")), 4.0)
