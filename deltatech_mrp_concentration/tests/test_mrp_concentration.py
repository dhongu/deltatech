# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestMrpConcentration(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Produse
        cls.product_final = cls.env["product.product"].create(
            {"name": "Final Product", "type": "consu", "is_storable": True}
        )
        cls.ingredient_primary = cls.env["product.product"].create(
            {"name": "Primary Ingredient", "type": "consu", "is_storable": True}
        )
        cls.ingredient_secondary = cls.env["product.product"].create(
            {"name": "Secondary Ingredient", "type": "consu", "is_storable": True}
        )

        # BoM
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.product_final.product_tmpl_id.id,
                "product_qty": 100.0,
                "type": "normal",
                "concentration": 10.0,
                "concentration_primary": 50.0,
            }
        )
        cls.bom_line_primary = cls.env["mrp.bom.line"].create(
            {
                "bom_id": cls.bom.id,
                "product_id": cls.ingredient_primary.id,
                "product_qty": 20.0,
                "ingredient_type": "primary",
            }
        )
        cls.bom_line_secondary = cls.env["mrp.bom.line"].create(
            {
                "bom_id": cls.bom.id,
                "product_id": cls.ingredient_secondary.id,
                "product_qty": 80.0,
                "ingredient_type": "secondary",
            }
        )

    def test_01_bom_concentration_onchange(self):
        """Test onchange logic on BoM"""
        # Simulăm onchange
        # Cantitate produs finit = 100, Conc finit = 20, Conc primar = 50
        # Rezultat așteptat primar: 100 * 20 / 50 = 40
        # Rezultat așteptat secundar: 100 - 40 = 60

        self.bom.concentration = 20.0
        self.bom._onchange_concentration_primary()

        self.assertEqual(self.bom_line_primary.product_qty, 40.0)
        self.assertEqual(self.bom_line_secondary.product_qty, 60.0)

    def test_02_production_concentration_onchange(self):
        """Test onchange logic on Production Order"""
        production = self.env["mrp.production"].create(
            {
                "product_id": self.product_final.id,
                "bom_id": self.bom.id,
                "product_qty": 100.0,
            }
        )
        # Simulăm selectarea BoM
        production._onchange_bom_id()
        self.assertEqual(production.concentration, 10.0)

        # Simulăm crearea liniilor de consum (move_raw_ids)
        # În mod normal Odoo le creează automat, dar aici le creăm manual pentru testul de onchange
        move_primary = self.env["stock.move"].create(
            {
                "raw_material_production_id": production.id,
                "product_id": self.ingredient_primary.id,
                "product_uom_qty": 20.0,
                "bom_line_id": self.bom_line_primary.id,
                "location_id": production.location_src_id.id,
                "location_dest_id": self.product_final.property_stock_production.id,
            }
        )
        move_secondary = self.env["stock.move"].create(
            {
                "raw_material_production_id": production.id,
                "product_id": self.ingredient_secondary.id,
                "product_uom_qty": 80.0,
                "bom_line_id": self.bom_line_secondary.id,
                "location_id": production.location_src_id.id,
                "location_dest_id": self.product_final.property_stock_production.id,
            }
        )

        production.move_raw_ids = [(6, 0, [move_primary.id, move_secondary.id])]

        # Schimbăm concentrația la 25
        # 100 * 25 / 50 = 50 (primar)
        # 100 - 50 = 50 (secundar)
        production.concentration = 25.0
        production._onchange_concentration_primary()

        self.assertEqual(move_primary.product_uom_qty, 50.0)
        self.assertEqual(move_secondary.product_uom_qty, 50.0)
