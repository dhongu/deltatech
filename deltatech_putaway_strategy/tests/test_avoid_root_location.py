from unittest.mock import patch

from odoo.fields import Domain
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAvoidRootLocationOnReservation(TransactionCase):
    """Test de regresie pentru `avoid_root_location_on_reservation`.

    Flagul de pe tipul de operație trebuie să ajungă, prin cheia de context
    `exclude_location_ids`, până în `stock.quant._get_gather_domain`, astfel încât
    stocul aflat direct în rădăcina depozitului (ex. `D1/S`) să nu fie rezervat
    automat pe livrări. Sublocațiile (rafturile) rămân eligibile.

    Consumatorul real al contextului este `deltatech_stock_removal_priority`, care nu
    este dependență a acestui modul; testul îl emulează prin patch, ca lanțul complet
    flag -> context -> domeniu -> rezervare să fie verificat aici.
    """

    def setUp(self):
        super().setUp()
        self.Quant = self.env["stock.quant"].sudo()
        StockLocation = self.env["stock.location"].sudo()

        # Rădăcina depozitului + un raft dedesubt
        self.root_loc = StockLocation.create({"name": "ROOT-S", "usage": "internal"})
        self.shelf_loc = StockLocation.create(
            {"name": "SHELF-A-001", "usage": "internal", "location_id": self.root_loc.id}
        )
        self.customer_loc = self.env.ref("stock.stock_location_customers")

        self.product = (
            self.env["product.product"].sudo().create({"name": "Test Avoid Root Location", "is_storable": True})
        )

        # Stoc identic în rădăcină și pe raft: fără excludere, strategia implicită
        # ia din rădăcină (quant creat primul); cu excludere trebuie să ia de pe raft.
        self.Quant._update_available_quantity(self.product, self.root_loc, 10)
        self.Quant._update_available_quantity(self.product, self.shelf_loc, 10)

        out_type = self.env["stock.picking.type"].sudo().search([("code", "=", "outgoing")], limit=1)
        self.assertTrue(out_type, "Nu există tip de operație de livrare în baza de test")
        self.picking_type = out_type.copy(
            {
                "name": "Test Delivery Avoid Root",
                "default_location_src_id": self.root_loc.id,
                "default_location_dest_id": self.customer_loc.id,
                # Explicit: rezervarea are loc la confirmare, ca în configurația PTC.
                "reservation_method": "at_confirm",
            }
        )

    def _new_picking(self, qty=10):
        """Creează livrarea *neconfirmată*: cu `reservation_method = at_confirm`,
        rezervarea (deci și `_action_assign`) se declanșează la `action_confirm`."""
        picking = (
            self.env["stock.picking"]
            .sudo()
            .create(
                {
                    "picking_type_id": self.picking_type.id,
                    "location_id": self.root_loc.id,
                    "location_dest_id": self.customer_loc.id,
                }
            )
        )
        self.env["stock.move"].sudo().create(
            {
                "product_id": self.product.id,
                "product_uom": self.product.uom_id.id,
                "product_uom_qty": qty,
                "picking_id": picking.id,
                "location_id": self.root_loc.id,
                "location_dest_id": self.customer_loc.id,
            }
        )
        return picking

    def _patch_gather_domain(self, side_effect):
        """Înlocuiește `stock.quant._get_gather_domain` cu un wrapper care primește
        metoda originală, ca testul să poată spiona sau altera domeniul."""
        Quant = type(self.env["stock.quant"])
        original = Quant._get_gather_domain

        def wrapper(quant_self, *args, **kwargs):
            return side_effect(original, quant_self, *args, **kwargs)

        return patch.object(Quant, "_get_gather_domain", wrapper)

    def _capture_gather_contexts(self, picking):
        """Confirmă livrarea (declanșând rezervarea) și întoarce valorile
        `exclude_location_ids` văzute de fiecare apel al `_get_gather_domain`."""
        captured = []

        def spy(original, quant_self, *args, **kwargs):
            captured.append(quant_self.env.context.get("exclude_location_ids"))
            return original(quant_self, *args, **kwargs)

        with self._patch_gather_domain(spy):
            picking.action_confirm()
            picking.action_assign()
        return captured

    def test_context_injected_when_flag_on(self):
        """Flag activ -> `exclude_location_ids` ajunge în `_get_gather_domain`."""
        self.picking_type.avoid_root_location_on_reservation = True
        captured = self._capture_gather_contexts(self._new_picking())

        self.assertTrue(captured, "`_get_gather_domain` nu a fost apelat la rezervare")
        self.assertTrue(
            any(self.root_loc.id in (ctx or []) for ctx in captured),
            "Locația rădăcină nu a fost transmisă prin `exclude_location_ids`; "
            "producătorul din `_action_assign` lipsește sau nu se aplică",
        )

    def test_context_not_injected_when_flag_off(self):
        """Flag inactiv -> comportament standard, fără excluderi."""
        self.picking_type.avoid_root_location_on_reservation = False
        captured = self._capture_gather_contexts(self._new_picking())

        self.assertTrue(captured, "`_get_gather_domain` nu a fost apelat la rezervare")
        self.assertFalse(
            [ctx for ctx in captured if ctx],
            "Nu trebuie transmis `exclude_location_ids` când flagul este inactiv",
        )

    def test_incoming_type_is_not_affected(self):
        """Excluderea vizează doar livrările, nu recepțiile."""
        self.picking_type.avoid_root_location_on_reservation = True
        self.picking_type.code = "incoming"
        captured = self._capture_gather_contexts(self._new_picking())

        self.assertFalse(
            [ctx for ctx in captured if ctx],
            "Excluderea nu trebuie aplicată pentru tipuri care nu sunt de livrare",
        )

    def test_reservation_skips_root_location(self):
        """Lanț complet: cu consumatorul activ, rezervarea ia de pe raft, nu din rădăcină."""
        self.picking_type.avoid_root_location_on_reservation = True
        picking = self._new_picking(qty=10)

        def consumer(original, quant_self, *args, **kwargs):
            # Emulează `deltatech_stock_removal_priority._get_gather_domain`
            domain = original(quant_self, *args, **kwargs)
            exclude = quant_self.env.context.get("exclude_location_ids")
            if exclude:
                domain = Domain.AND([domain, Domain("location_id", "not in", exclude)])
            return domain

        with self._patch_gather_domain(consumer):
            picking.action_confirm()
            picking.action_assign()

        move_lines = picking.move_ids.move_line_ids
        self.assertTrue(move_lines, "Rezervarea nu a produs linii de mișcare")
        self.assertEqual(
            move_lines.location_id,
            self.shelf_loc,
            "Rezervarea trebuie să ia stocul de pe raft, nu din rădăcina depozitului",
        )
        self.assertEqual(sum(move_lines.mapped("quantity")), 10)
        self.assertEqual(
            self.Quant._get_available_quantity(self.product, self.root_loc, strict=True),
            10,
            "Stocul din rădăcină trebuie să rămână nerezervat",
        )

    def test_reservation_uses_root_without_the_flag(self):
        """Contra-probă: fără flag, rădăcina este folosită (comportament standard)."""
        self.picking_type.avoid_root_location_on_reservation = False
        picking = self._new_picking(qty=10)
        picking.action_confirm()
        picking.action_assign()

        move_lines = picking.move_ids.move_line_ids
        self.assertTrue(move_lines, "Rezervarea nu a produs linii de mișcare")
        self.assertIn(
            self.root_loc,
            move_lines.location_id,
            "Fără flag, rezervarea standard trebuie să poată lua din rădăcină",
        )
