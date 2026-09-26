# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestProductReplenishReference(TransactionCase):
    """Câmpul "Grupare" (stock.reference) din wizard-ul de reaprovizionare produs,
    reintrodus în 19.0 în locul lui `procurement.group`, cu grupare zilnică automată.
    """

    def setUp(self):
        super().setUp()
        self.warehouse = self.env["stock.warehouse"].search([("company_id", "=", self.env.company.id)], limit=1)

        self.source_location = self.env["stock.location"].create(
            {
                "name": "Grupare source location",
                "location_id": self.warehouse.view_location_id.id,
                "usage": "internal",
            }
        )
        self.route = self.env["stock.route"].create(
            {
                "name": "Test pull route (grupare)",
                "rule_ids": [
                    Command.create(
                        {
                            "name": "Pull from grupare source location",
                            "location_src_id": self.source_location.id,
                            "location_dest_id": self.warehouse.lot_stock_id.id,
                            "company_id": self.env.company.id,
                            "action": "pull",
                            "auto": "manual",
                            "picking_type_id": self.warehouse.int_type_id.id,
                        }
                    )
                ],
            }
        )
        self.product_a = self.env["product.product"].create(
            {"name": "Test grupare A", "is_storable": True, "route_ids": [Command.set([self.route.id])]}
        )
        self.product_b = self.env["product.product"].create(
            {"name": "Test grupare B", "is_storable": True, "route_ids": [Command.set([self.route.id])]}
        )

    def _replenish(self, product, quantity=5.0):
        wizard = (
            self.env["product.replenish"]
            .with_context(default_product_id=product.id)
            .create(
                {
                    "product_id": product.id,
                    "product_tmpl_id": product.product_tmpl_id.id,
                    "uom_id": product.uom_id.id,
                    "quantity": quantity,
                    "warehouse_id": self.warehouse.id,
                    "route_id": self.route.id,
                }
            )
        )
        wizard.launch_replenishment()
        return wizard

    def test_daily_reference_is_auto_filled(self):
        wizard = self._replenish(self.product_a)
        self.assertTrue(wizard.reference_id, "Wizard-ul ar trebui să completeze singur referința zilnică")
        self.assertIn(self.warehouse.code or self.warehouse.name, wizard.reference_id.name)

    def test_same_day_same_warehouse_shares_reference_and_picking(self):
        """Două reaprovizionări, produse diferite, aceeași zi, același depozit
        -> aceeași referință și, prin ea, același stock.picking."""
        wizard_a = self._replenish(self.product_a)
        wizard_b = self._replenish(self.product_b)

        self.assertEqual(
            wizard_a.reference_id,
            wizard_b.reference_id,
            "Aceeași zi + același depozit ar trebui să folosească aceeași grupare",
        )

        move_a = self.env["stock.move"].search([("product_id", "=", self.product_a.id)], limit=1)
        move_b = self.env["stock.move"].search([("product_id", "=", self.product_b.id)], limit=1)
        self.assertTrue(move_a, "Reaprovizionarea produsului A ar trebui să genereze o mutare")
        self.assertTrue(move_b, "Reaprovizionarea produsului B ar trebui să genereze o mutare")
        self.assertIn(wizard_a.reference_id, move_a.reference_ids)
        self.assertIn(wizard_b.reference_id, move_b.reference_ids)

        self.assertTrue(move_a.picking_id, "Mutarea A ar trebui asignată pe un stock.picking")
        self.assertTrue(move_b.picking_id, "Mutarea B ar trebui asignată pe un stock.picking")
        self.assertEqual(
            move_a.picking_id,
            move_b.picking_id,
            "Cele două reaprovizionări din aceeași zi ar trebui unite pe un singur document",
        )

    def test_different_warehouses_get_different_reference(self):
        other_warehouse = self.env["stock.warehouse"].create({"name": "Alt depozit grupare", "code": "AGR"})
        wizard_a = self._replenish(self.product_a)

        wizard_other = (
            self.env["product.replenish"]
            .with_context(default_product_id=self.product_a.id)
            .create(
                {
                    "product_id": self.product_a.id,
                    "product_tmpl_id": self.product_a.product_tmpl_id.id,
                    "uom_id": self.product_a.uom_id.id,
                    "quantity": 1.0,
                    "warehouse_id": other_warehouse.id,
                }
            )
        )
        wizard_other._onchange_warehouse_id_reference()

        self.assertNotEqual(
            wizard_a.reference_id,
            wizard_other.reference_id,
            "Depozite diferite nu ar trebui să împartă aceeași grupare zilnică",
        )

    def test_duplicate_replenish_same_day_same_product_is_blocked(self):
        wizard_a = self._replenish(self.product_a)
        move_a = self.env["stock.move"].search([("product_id", "=", self.product_a.id)], limit=1)
        # Simulăm finalizarea mutării, fără a rula tot fluxul de disponibilitate de stoc.
        move_a.write({"state": "done"})

        wizard_repeat = (
            self.env["product.replenish"]
            .with_context(default_product_id=self.product_a.id)
            .create(
                {
                    "product_id": self.product_a.id,
                    "product_tmpl_id": self.product_a.product_tmpl_id.id,
                    "uom_id": self.product_a.uom_id.id,
                    "quantity": 3.0,
                    "warehouse_id": self.warehouse.id,
                    "route_id": self.route.id,
                    "reference_id": wizard_a.reference_id.id,
                }
            )
        )
        with self.assertRaises(UserError):
            wizard_repeat.launch_replenishment()

        # Un alt produs, aceeași grupare, nu trebuie blocat.
        wizard_b = self._replenish(self.product_b)
        self.assertTrue(wizard_b.reference_id)
