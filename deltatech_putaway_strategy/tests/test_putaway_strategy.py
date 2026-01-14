from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPutawayStrategy(TransactionCase):
    def setUp(self):
        super().setUp()
        self.StockLocation = self.env["stock.location"].sudo()
        self.Product = self.env["product.product"].sudo()
        self.Quant = self.env["stock.quant"].sudo()

        # Creează o locație părinte și două frunze interne
        self.parent_loc = self.StockLocation.create(
            {
                "name": "PARENT",
                "usage": "internal",
            }
        )
        self.loc1 = self.StockLocation.create(
            {
                "name": "L1",
                "usage": "internal",
                "location_id": self.parent_loc.id,
                "max_products_leaf": 5,
            }
        )
        self.loc2 = self.StockLocation.create(
            {
                "name": "L2",
                "usage": "internal",
                "location_id": self.parent_loc.id,
                "max_products_leaf": 5,
            }
        )

        # Creează un produs simplu
        self.product = self.Product.create(
            {
                "name": "Test Product",
                "type": "product",
            }
        )

        # Ocupă parțial L1 cu 2 bucăți
        self.Quant.create(
            {
                "product_id": self.product.id,
                "location_id": self.loc1.id,
                "quantity": 2.0,
            }
        )

    def test_check_can_be_used_capacity(self):
        self.assertTrue(self.loc1._check_can_be_used(self.product, quantity=5))

        self.Quant.create(
            {
                "product_id": self.product.id,
                "location_id": self.loc2.id,
                "quantity": 5.0,
            }
        )
        self.assertFalse(self.loc2._check_can_be_used(self.product, quantity=5))

    # def test_get_putaway_prefers_empty_child(self):
    #     # Putaway pe părinte cu qty 1 ar trebui să aleagă L1 (goală) înaintea lui L2 (ocupată)
    #     dest = self.parent_loc._get_putaway_strategy(self.product, quantity=1)
    #     self.assertEqual(dest.id, self.loc1.id)

    def test_in_stock(self):
        # se face in picking de receptie in care se verifica intrarea in stoc a 7 bucati
        # se verifica ca se umple prima celula cu 5 buc si restul se va pune pe a doua celula

        # Golim locațiile pentru un test curat

        self.loc1._compute_warehouse_occupancy()
        self.loc2._compute_warehouse_occupancy()

        # Căutăm un tip de operație de intrare
        picking_type = self.env["stock.picking.type"].search(
            [("code", "=", "incoming"), ("warehouse_id", "!=", False)], limit=1
        )
        if not picking_type:
            picking_type = self.env.ref("stock.picking_type_in")

        supplier_location = self.env.ref("stock.stock_location_suppliers")

        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": supplier_location.id,
                "location_dest_id": self.parent_loc.id,
            }
        )

        self.env["stock.move"].create(
            {
                "name": "Test Move",
                "product_id": self.product.id,
                "product_uom_qty": 7,
                "product_uom": self.product.uom_id.id,
                "picking_id": picking.id,
                "location_id": supplier_location.id,
                "location_dest_id": self.parent_loc.id,
            }
        )

        picking.action_confirm()
        picking.action_assign()

        # Verificăm distribuția
        lines_in_loc1 = picking.move_line_ids.filtered(lambda l: l.location_dest_id == self.loc1)
        lines_in_loc2 = picking.move_line_ids.filtered(lambda l: l.location_dest_id == self.loc2)

        qty_in_loc1 = sum(lines_in_loc1.mapped("quantity"))
        qty_in_loc2 = sum(lines_in_loc2.mapped("quantity"))

        self.assertEqual(qty_in_loc1, 3, "Locația 1 ar trebui să aibă 3 bucăți (capacitate maximă)")
        self.assertEqual(qty_in_loc2, 4, "Restul de 4 bucăți ar trebui să fie în locația 2")
