from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Creare atribut culoare
        cls.attribute_color = cls.env["product.attribute"].create(
            {"name": "Color", "display_type": "color", "create_variant": "always"}
        )
        cls.attr_val_red = cls.env["product.attribute.value"].create(
            {"name": "Red", "attribute_id": cls.attribute_color.id}
        )

        # Creare produse RAL
        cls.product_ral_red = cls.env["product.product"].create(
            {"name": "RAL Red", "default_code": "RAL Red", "is_storable": True}
        )
        cls.product_ral_0000 = cls.env["product.product"].create(
            {"name": "RAL Generic", "default_code": "RAL 0000", "is_storable": True}
        )

        # Creare produs finit cu atribut de culoare
        cls.product_finished = cls.env["product.template"].create(
            {
                "name": "Finished Product",
                "is_storable": True,
                "attribute_line_ids": [
                    (0, 0, {"attribute_id": cls.attribute_color.id, "value_ids": [(6, 0, [cls.attr_val_red.id])]})
                ],
            }
        )
        cls.product_finished_variant = cls.product_finished.product_variant_id

        # Creare BoM
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.product_finished.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [(0, 0, {"product_id": cls.product_ral_0000.id, "product_qty": 1.0})],
            }
        )

    def test_01_onchange_product_id(self):
        """Test dacă ral_id este setat corect la schimbarea produsului"""
        production = self.env["mrp.production"].new({"product_id": self.product_finished_variant.id})
        production._onchange_product_id()
        self.assertEqual(production.ral_id.id, self.product_ral_red.id, "RAL Red ar fi trebuit selectat automat")

    def test_02_onchange_ral_id(self):
        """Test dacă componentele RAL 0000 sunt înlocuite cu ral_id"""
        production = self.env["mrp.production"].create(
            {
                "product_id": self.product_finished_variant.id,
                "bom_id": self.bom.id,
                "product_qty": 1.0,
            }
        )
        # Forțăm RAL Red (în caz că onchange din create nu a mers cum ne așteptam sau vrem să testăm manual)
        production.ral_id = self.product_ral_red
        production.onchange_ral_id()

        for move in production.move_raw_ids:
            if move.bom_line_id.product_id == self.product_ral_0000:
                self.assertEqual(
                    move.product_id.id, self.product_ral_red.id, "Produsul de pe move ar fi trebuit să fie RAL Red"
                )

    def test_03_create_production(self):
        """Test crearea unei comenzi de producție și verificarea automată a RAL"""
        production = self.env["mrp.production"].create(
            {
                "product_id": self.product_finished_variant.id,
                "bom_id": self.bom.id,
                "product_qty": 1.0,
            }
        )
        self.assertEqual(production.ral_id.id, self.product_ral_red.id, "RAL Red ar fi trebuit setat la creare")
        for move in production.move_raw_ids:
            if move.bom_line_id.product_id == self.product_ral_0000:
                self.assertEqual(
                    move.product_id.id, self.product_ral_red.id, "Componenta RAL ar fi trebuit înlocuită la creare"
                )

    def test_05_substitution_survives_recompute(self):
        """RAL substituit trebuie să reziste recalculării componentelor (O19: move_raw_ids calculat)"""
        production = self.env["mrp.production"].create(
            {
                "product_id": self.product_finished_variant.id,
                "bom_id": self.bom.id,
                "product_qty": 1.0,
            }
        )
        production.ral_id = self.product_ral_red
        production.onchange_ral_id()
        # Modificarea cantității retrigăruiește _compute_move_raw_ids și regenerează componentele
        production.product_qty = 5.0
        ral_moves = production.move_raw_ids.filtered(lambda m: m.bom_line_id.product_id == self.product_ral_0000)
        self.assertTrue(ral_moves, "Ar fi trebuit să existe o mișcare pentru componenta RAL")
        for move in ral_moves:
            self.assertEqual(
                move.product_id.id,
                self.product_ral_red.id,
                "Substituția RAL trebuie păstrată după recalcularea componentelor",
            )

    def test_04_action_generate_serial(self):
        """Test propagarea RAL către lot"""
        production = self.env["mrp.production"].create(
            {
                "product_id": self.product_finished_variant.id,
                "bom_id": self.bom.id,
                "product_qty": 1.0,
            }
        )
        # Simulăm generarea de serial
        lot = self.env["stock.lot"].create(
            {"name": "LOT001", "product_id": self.product_finished_variant.id, "company_id": self.env.company.id}
        )
        production.lot_producing_ids = [Command.link(lot.id)]
        production.action_generate_serial()

        self.assertEqual(lot.ral_id.id, self.product_ral_red.id, "RAL ar fi trebuit propagat către lot")
