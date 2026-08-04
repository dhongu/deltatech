from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestCapacityAccessRights(TransactionCase):
    """Test de regresie: un simplu utilizator de stoc trebuie să poată opera stocul
    în locații cu capacitate configurată.

    `current_products` / `max_products` / `planned_products` sunt compute *nestocate*.
    Apelarea directă a metodelor de compute (în afara mașinăriei ORM) transformă
    atribuirile din ele în `write()` pe `stock.location`, operație permisă doar
    grupului Inventory/Administrator — deci validarea transferurilor cădea cu
    `AccessError` pentru `stock.group_stock_user`.
    """

    def setUp(self):
        super().setUp()
        StockLocation = self.env["stock.location"].sudo()

        self.stock_user = (
            self.env["res.users"]
            .sudo()
            .create(
                {
                    "name": "Operator Stoc",
                    "login": "test_operator_stoc",
                    # Odoo 19: `groups_id` a fost redenumit `group_ids`.
                    # Doar operator de stoc — NU Inventory/Administrator; multi-locations e
                    # necesar ca să poată lucra pe locații, ca operatorii reali.
                    "group_ids": [
                        (
                            6,
                            0,
                            [
                                self.env.ref("stock.group_stock_user").id,
                                self.env.ref("stock.group_stock_multi_locations").id,
                            ],
                        )
                    ],
                }
            )
        )
        self.assertFalse(
            self.stock_user.has_group("stock.group_stock_manager"),
            "Testul e valid doar dacă utilizatorul NU e administrator de stoc",
        )

        self.src_loc = StockLocation.create({"name": "SRC", "usage": "internal"})
        self.parent_loc = StockLocation.create({"name": "CAP-PARENT", "usage": "internal"})
        # Frunza cu capacitate — exact cazul care declanșa compute-urile manuale
        self.leaf_loc = StockLocation.create(
            {
                "name": "CAP-LEAF",
                "usage": "internal",
                "location_id": self.parent_loc.id,
                "max_products_leaf": 100,
            }
        )

        self.product = self.env["product.product"].sudo().create({"name": "Test Capacity Product", "is_storable": True})
        self.env["stock.quant"].sudo()._update_available_quantity(self.product, self.src_loc, 10)

        # Pe o bază fără demo, tipul de transfer intern al depozitului există dar e inactiv
        # (multi-locations dezactivat implicit), deci `search` simplu nu îl găsește.
        warehouse = self.env["stock.warehouse"].sudo().search([], limit=1)
        self.assertTrue(warehouse, "Nu există depozit în baza de test")
        self.picking_type = warehouse.int_type_id.sudo()
        self.assertTrue(self.picking_type, "Depozitul nu are tip de transfer intern")
        if not self.picking_type.active:
            self.picking_type.active = True

    def _make_picking(self, qty=10):
        picking = (
            self.env["stock.picking"]
            .sudo()
            .create(
                {
                    "picking_type_id": self.picking_type.id,
                    "location_id": self.src_loc.id,
                    "location_dest_id": self.leaf_loc.id,
                }
            )
        )
        self.env["stock.move"].sudo().create(
            {
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": qty,
                "picking_id": picking.id,
                "location_id": self.src_loc.id,
                "location_dest_id": self.leaf_loc.id,
            }
        )
        return picking

    def test_stock_user_can_validate_into_capacity_location(self):
        """Un `stock.group_stock_user` validează fără AccessError pe stock.location."""
        picking = self._make_picking()
        as_user = picking.with_user(self.stock_user)
        as_user.action_confirm()
        as_user.action_assign()
        for line in as_user.move_ids.move_line_ids:
            line.quantity = line.quantity or 10

        try:
            as_user.button_validate()
        except AccessError as e:
            self.fail(f"Utilizatorul de stoc nu ar trebui să primească AccessError la validare: {e}")

        self.assertEqual(picking.state, "done")

    def test_over_capacity_still_raises_business_error(self):
        """Bariera de capacitate din `_action_done` rămâne activă: UserError, nu AccessError.

        Capacitatea se reduce *după* asignare intenționat. Dacă e redusă înainte, splitarea
        din `_split_by_putaway_capacity` intră în buclă infinită (ramura `qty_available < 0`
        copiază linii cu aceeași destinație, iar garda de buclă nu le prinde) — defect
        preexistent, raportat separat, care nu trebuie să blocheze acest test.
        """
        picking = self._make_picking()
        as_user = picking.with_user(self.stock_user)
        as_user.action_confirm()
        as_user.action_assign()

        self.leaf_loc.sudo().max_products_leaf = 1

        with self.assertRaises(UserError) as cm:
            as_user.button_validate()
        self.assertNotIsInstance(
            cm.exception, AccessError, "Depășirea capacității trebuie raportată ca eroare de business"
        )

    def test_compute_read_does_not_require_admin(self):
        """Citirea metricilor de ocupare prin ORM nu cere drepturi de administrator.

        Aceasta e calea corectă (spre deosebire de apelarea directă a metodei de compute):
        ORM-ul rulează compute-ul în context protejat, deci atribuirile rămân în cache și
        nu devin `write()` pe `stock.location`.
        """
        leaf = self.leaf_loc.with_user(self.stock_user)
        leaf.invalidate_recordset(["current_products", "max_products", "occupancy_ratio"])
        try:
            current = leaf.current_products
            maximum = leaf.max_products
            ratio = leaf.occupancy_ratio
            planned = leaf.with_context(exclude_move_line_id=0).planned_products
        except AccessError as e:
            self.fail(f"Citirea câmpurilor calculate nu ar trebui să ceară drepturi de admin: {e}")

        self.assertEqual(maximum, 100, "max_products preia capacitatea frunzei")
        self.assertEqual(current, 0.0, "locația frunză e goală la început")
        self.assertEqual(ratio, 0.0)
        self.assertEqual(planned, 0.0)
