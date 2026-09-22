"""Mai multe linii pe aceeași validare, împărțind același stoc.

Verificarea rulează pe tot recordset-ul înainte ca `super()._action_done()` să
scrie ceva în quant-uri, deci fiecare linie citește același stoc neatins. Luate
una câte una, două linii de 1 pe un stoc de 1 sunt fiecare legale, iar
transferul ajunge totuși la -1 — așa a ajuns PTC pe stoc negativ de două ori
(tichetele 9184 și 9543), cu 2 bucăți selectate la raft când era una singură.

Testele de aici fixează atât blocarea cumulului, cât și granițele lui: linii pe
locații, produse, loturi, pachete sau proprietari diferiți nu au voie să se
adune între ele, altfel fixul ar bloca transferuri perfect valide.
"""

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestNegativeMultiline(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.write({"group_ids": [(4, cls.env.ref("stock.group_stock_multi_locations").id, 0)]})
        cls.env.company.no_negative_stock = True

        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.dest_location = cls.env.ref("stock.location_pack_zone")

        # A doua locatie interna, ca sa putem verifica ca liniile din locatii
        # diferite nu se aduna intre ele.
        cls.other_location = cls.env["stock.location"].create(
            {"name": "Shelf X", "usage": "internal", "location_id": cls.stock_location.id}
        )
        cls.free_location = cls.env["stock.location"].create(
            {
                "name": "Shelf Free",
                "usage": "internal",
                "location_id": cls.stock_location.id,
                "allow_negative_stock": True,
            }
        )

        cls.product = cls.env["product.product"].create({"name": "Product A", "is_storable": True})
        cls.product_b = cls.env["product.product"].create({"name": "Product B", "is_storable": True})
        cls.product_lot = cls.env["product.product"].create(
            {"name": "Product Lot", "is_storable": True, "tracking": "lot"}
        )
        cls.lot_a = cls.env["stock.lot"].create(
            {"name": "LOT-A", "product_id": cls.product_lot.id, "company_id": cls.env.company.id}
        )
        cls.lot_b = cls.env["stock.lot"].create(
            {"name": "LOT-B", "product_id": cls.product_lot.id, "company_id": cls.env.company.id}
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _stock(self, product, quantity, location=None, lot=None, package=None, owner=None):
        self.env["stock.quant"]._update_available_quantity(
            product_id=product,
            location_id=location or self.stock_location,
            quantity=quantity,
            lot_id=lot,
            package_id=package,
            owner_id=owner,
        )

    def _move(self, product, lines, location=None, uom=None):
        """O mișcare cu una sau mai multe linii, gata de validare.

        ``lines`` e o listă de dicturi cu ``quantity`` și, optional,
        ``lot_id`` / ``package_id`` / ``owner_id`` / ``location_id``.
        """
        source = location or self.stock_location
        move = self.env["stock.move"].create(
            {
                "location_id": source.id,
                "location_dest_id": self.dest_location.id,
                "product_id": product.id,
                "product_uom": (uom or self.uom_unit).id,
                "product_uom_qty": sum(line["quantity"] for line in lines),
            }
        )
        move._action_confirm()
        move.picked = True
        # Odoo poate genera singur linii la confirmare; le inlocuim cu ale
        # noastre, ca numarul si repartizarea lor sa fie exact cele din test.
        move.move_line_ids.unlink()
        for line in lines:
            vals = move._prepare_move_line_vals()
            vals.update(line)
            self.env["stock.move.line"].create(vals)
        return move

    def _assert_blocked(self, move):
        with self.assertRaises(UserError) as cm:
            move._action_done()
        self.assertRegex(cm.exception.args[0], "avoid negative stock")

    def _quantity(self, product, location=None, lot=None):
        domain = [
            ("product_id", "=", product.id),
            ("location_id", "=", (location or self.stock_location).id),
        ]
        if lot is not None:
            domain.append(("lot_id", "=", lot.id))
        return sum(self.env["stock.quant"].search(domain).mapped("quantity"))

    # ------------------------------------------------------------------
    # cazul din tichet
    # ------------------------------------------------------------------
    def test_two_lines_together_may_not_go_negative(self):
        """Cazul PTC: 1 bucata in stoc, doua linii de cate una."""
        self._stock(self.product, 1.0)
        move = self._move(self.product, [{"quantity": 1.0}, {"quantity": 1.0}])
        self._assert_blocked(move)
        self.assertEqual(self._quantity(self.product), 1.0, "stocul trebuie sa ramana neatins")

    def test_three_lines_together_may_not_go_negative(self):
        """Cumulul tine si peste doua linii; a treia e cea care rupe."""
        self._stock(self.product, 2.0)
        move = self._move(self.product, [{"quantity": 1.0}, {"quantity": 1.0}, {"quantity": 1.0}])
        self._assert_blocked(move)
        self.assertEqual(self._quantity(self.product), 2.0)

    def test_two_lines_that_fit_are_allowed(self):
        """Cat timp suma incape in stoc, transferul trece ca inainte."""
        self._stock(self.product, 2.0)
        move = self._move(self.product, [{"quantity": 1.0}, {"quantity": 1.0}])
        move._action_done()
        self.assertEqual(self._quantity(self.product), 0.0)

    def test_two_lines_that_exactly_empty_the_location_are_allowed(self):
        """Exact pe zero e permis — doar sub zero se blocheaza."""
        self._stock(self.product, 5.0)
        move = self._move(self.product, [{"quantity": 2.0}, {"quantity": 3.0}])
        move._action_done()
        self.assertEqual(self._quantity(self.product), 0.0)

    # ------------------------------------------------------------------
    # granitele cumulului: ce NU are voie sa se adune
    # ------------------------------------------------------------------
    def test_lines_from_different_locations_do_not_add_up(self):
        self._stock(self.product, 1.0, location=self.stock_location)
        self._stock(self.product, 1.0, location=self.other_location)
        move = self._move(
            self.product,
            [{"quantity": 1.0}, {"quantity": 1.0, "location_id": self.other_location.id}],
        )
        move._action_done()
        self.assertEqual(self._quantity(self.product, location=self.stock_location), 0.0)
        self.assertEqual(self._quantity(self.product, location=self.other_location), 0.0)

    def test_lines_of_different_products_do_not_add_up(self):
        self._stock(self.product, 1.0)
        self._stock(self.product_b, 1.0)
        move_a = self._move(self.product, [{"quantity": 1.0}])
        move_b = self._move(self.product_b, [{"quantity": 1.0}])
        # validate impreuna, ca intr-un transfer cu mai multe produse
        (move_a | move_b).move_line_ids._action_done()
        self.assertEqual(self._quantity(self.product), 0.0)
        self.assertEqual(self._quantity(self.product_b), 0.0)

    def test_lines_of_different_lots_do_not_add_up(self):
        self._stock(self.product_lot, 1.0, lot=self.lot_a)
        self._stock(self.product_lot, 1.0, lot=self.lot_b)
        move = self._move(
            self.product_lot,
            [{"quantity": 1.0, "lot_id": self.lot_a.id}, {"quantity": 1.0, "lot_id": self.lot_b.id}],
        )
        move._action_done()
        self.assertEqual(self._quantity(self.product_lot, lot=self.lot_a), 0.0)
        self.assertEqual(self._quantity(self.product_lot, lot=self.lot_b), 0.0)

    def test_two_lines_on_the_same_lot_may_not_go_negative(self):
        self._stock(self.product_lot, 1.0, lot=self.lot_a)
        move = self._move(
            self.product_lot,
            [{"quantity": 1.0, "lot_id": self.lot_a.id}, {"quantity": 1.0, "lot_id": self.lot_a.id}],
        )
        self._assert_blocked(move)
        self.assertEqual(self._quantity(self.product_lot, lot=self.lot_a), 1.0)

    def test_lines_of_different_packages_do_not_add_up(self):
        package_a = self.env["stock.package"].create({"name": "PKG-A"})
        package_b = self.env["stock.package"].create({"name": "PKG-B"})
        self._stock(self.product, 1.0, package=package_a)
        self._stock(self.product, 1.0, package=package_b)
        move = self._move(
            self.product,
            [
                {"quantity": 1.0, "package_id": package_a.id},
                {"quantity": 1.0, "package_id": package_b.id},
            ],
        )
        move._action_done()
        self.assertEqual(self._quantity(self.product), 0.0)

    def test_two_lines_on_the_same_package_may_not_go_negative(self):
        package = self.env["stock.package"].create({"name": "PKG-A"})
        self._stock(self.product, 1.0, package=package)
        move = self._move(
            self.product,
            [{"quantity": 1.0, "package_id": package.id}, {"quantity": 1.0, "package_id": package.id}],
        )
        self._assert_blocked(move)
        self.assertEqual(self._quantity(self.product), 1.0)

    # ------------------------------------------------------------------
    # cumulul respecta unitatea de masura si comutatoarele existente
    # ------------------------------------------------------------------
    def test_lines_in_different_uom_accumulate_in_the_product_uom(self):
        """O duzina + o bucata pe un stoc de 12 depaseste cu una."""
        self._stock(self.product, 12.0)
        move = self.env["stock.move"].create(
            {
                "location_id": self.stock_location.id,
                "location_dest_id": self.dest_location.id,
                "product_id": self.product.id,
                "product_uom": self.uom_unit.id,
                "product_uom_qty": 13.0,
            }
        )
        move._action_confirm()
        move.picked = True
        move.move_line_ids.unlink()
        vals = move._prepare_move_line_vals()
        self.env["stock.move.line"].create({**vals, "product_uom_id": self.uom_dozen.id, "quantity": 1.0})
        self.env["stock.move.line"].create({**vals, "product_uom_id": self.uom_unit.id, "quantity": 1.0})
        self._assert_blocked(move)
        self.assertEqual(self._quantity(self.product), 12.0)

    def test_a_location_allowing_negative_stock_is_still_exempt(self):
        self._stock(self.product, 1.0, location=self.free_location)
        move = self._move(self.product, [{"quantity": 1.0}, {"quantity": 1.0}], location=self.free_location)
        move._action_done()
        self.assertEqual(self._quantity(self.product, location=self.free_location), -1.0)

    def test_the_company_switch_still_turns_the_whole_check_off(self):
        self.env.company.no_negative_stock = False
        self._stock(self.product, 1.0)
        move = self._move(self.product, [{"quantity": 1.0}, {"quantity": 1.0}])
        move._action_done()
        self.assertEqual(self._quantity(self.product), -1.0)

    def test_an_incoming_line_is_not_checked_and_does_not_consume(self):
        """Liniile care intra in locatie nu sunt verificate.

        Sursa lor e alta locatie, deci nu au ce consuma din cea de destinatie;
        cumulul nu trebuie sa le numere.
        """
        self._stock(self.product, 1.0, location=self.other_location)
        move = self.env["stock.move"].create(
            {
                "location_id": self.other_location.id,
                "location_dest_id": self.stock_location.id,
                "product_id": self.product.id,
                "product_uom": self.uom_unit.id,
                "product_uom_qty": 1.0,
            }
        )
        move._action_confirm()
        move.picked = True
        move.move_line_ids.unlink()
        self.env["stock.move.line"].create({**move._prepare_move_line_vals(), "quantity": 1.0})
        move._action_done()
        self.assertEqual(self._quantity(self.product, location=self.stock_location), 1.0)
        self.assertEqual(self._quantity(self.product, location=self.other_location), 0.0)
