"""Produse cu numere de serie pe o locatie cu "Check Serial No." debifat.

Cu verificarea seriei oprita, controlul de stoc negativ trebuie sa se uite la
cantitatea fizica a produsului pe toate seriile din locatie (pastrand filtrele
de pachet si proprietar), nu la quant-urile fara serie. Inainte de fix,
domeniul cerea explicit `lot_id = False`, deci excludea tocmai quant-urile cu
serie si bloca un transfer legitim (STOCK-001).
"""

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestNegativeSerial(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.no_negative_stock = True

        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.dest_location = cls.env.ref("stock.location_pack_zone")

        cls.location = cls.env["stock.location"].create(
            {
                "name": "Shelf Serial",
                "usage": "internal",
                "location_id": cls.stock_location.id,
                "check_serial_no": False,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Product Serial", "is_storable": True, "tracking": "serial"}
        )
        cls.sn_1, cls.sn_2 = cls.env["stock.lot"].create(
            [
                {"name": "SN-1", "product_id": cls.product.id, "company_id": cls.env.company.id},
                {"name": "SN-2", "product_id": cls.product.id, "company_id": cls.env.company.id},
            ]
        )

    def _stock(self, lot, location=None):
        self.env["stock.quant"]._update_available_quantity(
            product_id=self.product, location_id=location or self.location, quantity=1.0, lot_id=lot
        )

    def _move(self, lots, location=None):
        move = self.env["stock.move"].create(
            {
                "location_id": (location or self.location).id,
                "location_dest_id": self.dest_location.id,
                "product_id": self.product.id,
                "uom_id": self.uom_unit.id,
                "product_uom_qty": len(lots),
            }
        )
        move._action_confirm()
        move.picked = True
        move.move_line_ids.unlink()
        for lot in lots:
            vals = move._prepare_move_line_vals()
            vals.update({"quantity": 1.0, "lot_id": lot.id})
            self.env["stock.move.line"].create(vals)
        return move

    def _assert_blocked(self, move):
        with self.assertRaises(UserError) as cm:
            move._action_done()
        self.assertRegex(cm.exception.args[0], "avoid negative stock")

    def _quantity(self, location=None):
        quants = self.env["stock.quant"].search(
            [("product_id", "=", self.product.id), ("location_id", "=", (location or self.location).id)]
        )
        return sum(quants.mapped("quantity"))

    # ------------------------------------------------------------------
    # Check Serial No. debifat: stocul se aduna pe toate seriile
    # ------------------------------------------------------------------
    def test_serial_check_off_available_serial_is_not_blocked(self):
        """Cazul din STOCK-001: o bucata cu serie in stoc, o linie pe ea."""
        self._stock(self.sn_1)
        move = self._move(self.sn_1)
        move._action_done()
        self.assertEqual(self._quantity(), 0.0)

    def test_serial_check_off_two_serials_two_lines_are_allowed(self):
        self._stock(self.sn_1)
        self._stock(self.sn_2)
        move = self._move(self.sn_1 | self.sn_2)
        move._action_done()
        self.assertEqual(self._quantity(), 0.0)

    def test_serial_check_off_lines_add_up_across_serials(self):
        """Doua linii pe serii diferite consuma acelasi stoc agregat de 1."""
        self._stock(self.sn_1)
        move = self._move(self.sn_1 | self.sn_2)
        self._assert_blocked(move)
        self.assertEqual(self._quantity(), 1.0, "stocul trebuie sa ramana neatins")

    def test_serial_check_off_absent_serial_passes_on_the_total(self):
        """Fara verificarea seriei, conteaza doar totalul: o serie absenta trece.

        Comportament asumat, documentat in fisa: nucleul descarca apoi seria de
        pe linie, care ramane pe -1, iar seria reala ramane pe +1.
        """
        self._stock(self.sn_1)
        move = self._move(self.sn_2)
        move._action_done()
        self.assertEqual(self._quantity(), 0.0)

    def test_serial_check_off_inventory_fix_needs_two_steps(self):
        """Dupa o serie absenta (SN-2 pe -1, SN-1 pe +1), inventarul se aplica in doi pasi.

        Aplicate impreuna, minusul pe SN-1 e verificat pe totalul locatiei (0) si e
        blocat; plusul pe SN-2 vine din locatia de inventar si nu e numarat.
        Intai plusul, apoi minusul: trece. Ordinea e descrisa in fisa (pasul 7).
        """
        self._stock(self.sn_1)
        self._move(self.sn_2)._action_done()
        Quant = self.env["stock.quant"]
        domain = [("product_id", "=", self.product.id), ("location_id", "=", self.location.id)]
        quant_1 = Quant.search(domain + [("lot_id", "=", self.sn_1.id)])
        quant_2 = Quant.search(domain + [("lot_id", "=", self.sn_2.id)])
        self.assertEqual((quant_1.quantity, quant_2.quantity), (1.0, -1.0))

        (quant_1 | quant_2).inventory_quantity = 0.0
        with self.assertRaisesRegex(UserError, "avoid negative stock"):
            (quant_1 | quant_2).action_apply_inventory()

        quant_2.inventory_quantity = 0.0
        quant_2.action_apply_inventory()
        quant_1.inventory_quantity = 0.0
        quant_1.action_apply_inventory()
        self.assertEqual((quant_1.quantity, quant_2.quantity), (0.0, 0.0))

    def test_serial_check_off_other_location_does_not_count(self):
        """Agregarea pe serii nu scoate filtrul de locatie."""
        self._stock(self.sn_1, location=self.stock_location)
        move = self._move(self.sn_1)
        self._assert_blocked(move)

    # ------------------------------------------------------------------
    # Check Serial No. bifat (implicit): verificarea ramane pe serie
    # ------------------------------------------------------------------
    def test_serial_check_on_available_serial_is_allowed(self):
        self.location.check_serial_no = True
        self._stock(self.sn_1)
        move = self._move(self.sn_1)
        move._action_done()
        self.assertEqual(self._quantity(), 0.0)

    def test_serial_check_on_missing_serial_is_blocked(self):
        self.location.check_serial_no = True
        self._stock(self.sn_1)
        move = self._move(self.sn_2)
        self._assert_blocked(move)
