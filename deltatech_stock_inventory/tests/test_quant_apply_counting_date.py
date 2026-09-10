# ©  2015-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.tests.common import TransactionCase


class TestQuantApplyCountingDate(TransactionCase):
    """Ajustarea aplicata din wizardul standard trimite data de numarare pozitional
    catre stock.quant.action_apply_inventory; overrideul nostru trebuie sa o accepte."""

    def setUp(self):
        super().setUp()
        self.env.user.group_ids |= self.env.ref("deltatech_stock_inventory.group_view_inventory_button")
        self.location = self.env["stock.location"].create({"name": "Counting Date Loc", "usage": "internal"})
        self.product = self.env["product.product"].create(
            {"name": "Counting Date Product", "is_storable": True, "standard_price": 7.0}
        )
        self.quant = (
            self.env["stock.quant"]
            .with_context(inventory_mode=True)
            .create(
                {
                    "product_id": self.product.id,
                    "location_id": self.location.id,
                    "inventory_quantity": 3.0,
                }
            )
        )

    def test_apply_from_wizard_with_counting_date(self):
        counting_date = fields.Datetime.to_datetime("2026-01-15 08:00:00")
        wizard = self.env["stock.inventory.adjustment.name"].create(
            {
                "quant_ids": [(6, 0, self.quant.ids)],
                "inventory_adjustment_name": "Inventar test",
                "counting_date": counting_date,
            }
        )
        wizard.action_apply()

        self.assertEqual(self.quant.quantity, 3.0)
        inventory = self.env["stock.inventory"].search([("name", "=", "Inventar test")], limit=1)
        self.assertTrue(inventory, "Ajustarea trebuie sa genereze documentul de inventar")
        self.assertEqual(inventory.state, "done")
        # Documentul si mișcarile poarta data de numarare, nu data de azi
        self.assertEqual(inventory.date, counting_date)
        move = self.env["stock.move"].search([("product_id", "=", self.product.id), ("state", "=", "done")], limit=1)
        self.assertEqual(move.date, counting_date)

    def test_apply_without_date_still_works(self):
        self.quant.with_context(inventory_mode=True).action_apply_inventory()
        self.assertEqual(self.quant.quantity, 3.0)
