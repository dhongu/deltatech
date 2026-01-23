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
        self.assertTrue(self.loc1._check_can_be_used(self.product, quantity=3))
        self.assertFalse(self.loc1._check_can_be_used(self.product, quantity=4))

    def test_planned_quantity_occupancy(self):
        """Verifică dacă cantitățile planificate sunt luate în considerare separat."""
        # Curățăm locația L1 de stocul creat în setUp
        self.loc1.quant_ids.unlink()

        # Inițial locația este goală
        self.loc1._compute_warehouse_occupancy()
        self.assertEqual(self.loc1.current_products, 0.0)
        self.assertEqual(self.loc1.planned_products, 0.0)
        self.assertTrue(self.loc1._check_can_be_used(self.product, quantity=1))

        # Creăm o mișcare de stoc planificată (recepție) către loc1
        supplier_location = self.env.ref("stock.stock_location_suppliers")
        picking_type = self.env["stock.picking.type"].search([("code", "=", "incoming")], limit=1)
        if not picking_type:
            picking_type = self.env.ref("stock.picking_type_in")

        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": supplier_location.id,
                "location_dest_id": self.loc1.id,
            }
        )

        self.env["stock.move"].create(
            {
                "name": "Test Planned Move",
                "product_id": self.product.id,
                "product_uom_qty": 5,
                "product_uom": self.product.uom_id.id,
                "picking_id": picking.id,
                "location_id": supplier_location.id,
                "location_dest_id": self.loc1.id,
            }
        )

        picking.action_confirm()
        # Nu validăm picking-ul, deci marfa este doar "planificată" (incoming)

        # Recalculăm ocuparea
        self.loc1._compute_planned_products()
        self.loc1._compute_warehouse_occupancy()

        self.assertEqual(self.loc1.current_products, 0.0, "Cantitatea curentă ar trebui să fie 0 (nu e încă în stoc)")
        self.assertEqual(self.loc1.planned_products, 5.0, "Cantitatea planificată ar trebui să fie 5")
        self.assertEqual(self.loc1.occupancy_ratio, 0.0, "Raportul de ocupare ar trebui să fie 0 (doar stoc fizic)")

        # Ar trebui să returneze False pentru că locația este deja plină (planificat)
        self.assertFalse(
            self.loc1._check_can_be_used(self.product, quantity=1), "Locația ar trebui să fie considerată plină"
        )

    # def test_get_putaway_prefers_empty_child(self):
    #     # Putaway pe părinte cu qty 1 ar trebui să aleagă L1 (goală) înaintea lui L2 (ocupată)
    #     dest = self.parent_loc._get_putaway_strategy(self.product, quantity=1)
    #     self.assertEqual(dest.id, self.loc1.id)

    def test_picking_with_two_products_v2(self):
        """Test cu un picking cu 2 produse diferite, ambele adăugate înainte de confirmare.
        Acest test simulează fluxul real unde picking-ul este creat cu toate liniile și confirmat o singură dată.
        """
        # Creăm al doilea produs
        product2 = self.Product.create(
            {
                "name": "Test Product 2",
                "type": "product",
            }
        )

        # Golim locațiile
        self.loc1.quant_ids.unlink()
        self.loc2.quant_ids.unlink()

        # Setăm capacitatea la 2 pentru ambele locații
        self.loc1.write({"max_products_leaf": 2})
        self.loc2.write({"max_products_leaf": 2})

        # Căutăm un tip de operație de intrare
        picking_type = self.env["stock.picking.type"].search(
            [("code", "=", "incoming"), ("warehouse_id", "!=", False)], limit=1
        )
        if not picking_type:
            picking_type = self.env.ref("stock.picking_type_in")

        supplier_location = self.env.ref("stock.stock_location_suppliers")

        # Creăm picking-ul cu destinația părinte (pentru a lăsa strategia să decidă)
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": supplier_location.id,
                "location_dest_id": self.parent_loc.id,
            }
        )

        # Adăugăm primul produs - 2 bucăți către locația părinte
        self.env["stock.move"].create(
            {
                "name": "Move 1",
                "product_id": self.product.id,
                "product_uom_qty": 2,
                "product_uom": self.product.uom_id.id,
                "picking_id": picking.id,
                "location_id": supplier_location.id,
                "location_dest_id": self.parent_loc.id,
            }
        )

        # Adăugăm al doilea produs - 1 bucată către locația părinte
        self.env["stock.move"].create(
            {
                "name": "Move 2",
                "product_id": product2.id,
                "product_uom_qty": 1,
                "product_uom": product2.uom_id.id,
                "picking_id": picking.id,
                "location_id": supplier_location.id,
                "location_dest_id": self.parent_loc.id,
            }
        )

        # Confirmăm picking-ul (o singură dată)
        # Odoo va rula strategia de putaway în timpul confirmării/atribuirii (action_confirm / action_assign)
        picking.action_confirm()
        picking.action_assign()

        # Verificăm distribuția pentru product 1 (ar trebui să fie în L1)
        lines_p1 = picking.move_line_ids.filtered(lambda l: l.product_id == self.product)
        self.assertTrue(all(l.location_dest_id == self.loc1 for l in lines_p1), "Primul produs ar trebui să fie în L1")

        # Verificăm distribuția pentru product 2 (ar trebui să fie în L2)
        # Dacă logica funcționează corect, sistemul ar trebui să detecteze că L1 va fi plină de primul move și să trimită al doilea move în L2.
        lines_p2 = picking.move_line_ids.filtered(lambda l: l.product_id == product2)
        self.assertTrue(
            all(l.location_dest_id == self.loc2 for l in lines_p2), "Al doilea produs ar trebui să fie în L2"
        )
