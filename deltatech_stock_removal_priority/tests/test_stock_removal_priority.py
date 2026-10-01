# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "deltatech_stock_removal_priority")
class TestStockRemovalPriority(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "is_storable": True, "categ_id": cls.env.ref("product.product_category_goods").id}
        )

        cls.loc_1 = cls.env["stock.location"].create({"name": "Loc 1", "location_id": cls.stock_location.id})
        cls.loc_2 = cls.env["stock.location"].create({"name": "Loc 2", "location_id": cls.stock_location.id})
        cls.loc_3 = cls.env["stock.location"].create({"name": "Loc 3", "location_id": cls.stock_location.id})
        cls.env["stock.putaway.rule"].create(
            [
                {
                    "product_id": cls.product.id,
                    "location_in_id": cls.loc_1.id,
                    "location_out_id": cls.loc_2.id,
                    "sequence": 5,
                },
                {
                    "category_id": cls.product.categ_id.id,
                    "location_in_id": cls.loc_1.id,
                    "location_out_id": cls.loc_3.id,
                    "sequence": 7,
                },
            ]
        )

    def test_01_quant_priority_from_putaway(self):
        """Test ca prioritatea cuantului este luata din regula de putaway"""
        # Cream o regula de putaway

        # Cream un cuant
        quant = self.env["stock.quant"].create(
            {"product_id": self.product.id, "location_id": self.loc_2.id, "inventory_quantity": 10}
        )
        quant.action_apply_inventory()

        # Prioritatea ar trebui sa fie sequence-ul regulii de putaway (5)
        self.assertEqual(quant.removal_priority, 5)

    def test_03_quant_priority_from_category_putaway(self):
        """Daca nu exista regula pe produs, se foloseste regula pe categorie."""

        # Cream un cuant fara sa existe o regula pe produs
        quant = self.env["stock.quant"].create(
            {"product_id": self.product.id, "location_id": self.loc_3.id, "inventory_quantity": 3}
        )
        quant.action_apply_inventory()

        # Ar trebui sa ia prioritatea din regula pe categorie (7)
        self.assertEqual(quant.removal_priority, 7)

    def _make_quant(self, location, qty=4):
        quant = self.env["stock.quant"].create(
            {"product_id": self.product.id, "location_id": location.id, "inventory_quantity": qty}
        )
        quant.action_apply_inventory()
        return quant

    def _read_priority(self, quant):
        # citim valoarea stocata, nu cea din cache
        self.env.flush_all()
        quant.invalidate_recordset(["removal_priority"])
        return quant.removal_priority

    def test_04_category_change_recomputes_priority(self):
        """PRIORITY-001: schimbarea categoriei produsului recalculeaza prioritatea."""
        categ_b = self.env["product.category"].create({"name": "Categ B"})
        self.env["stock.putaway.rule"].create(
            {
                "category_id": categ_b.id,
                "location_in_id": self.loc_1.id,
                "location_out_id": self.loc_3.id,
                "sequence": 3,
            }
        )
        quant = self._make_quant(self.loc_3)
        self.assertEqual(self._read_priority(quant), 7)

        self.product.product_tmpl_id.categ_id = categ_b
        self.assertEqual(self._read_priority(quant), 3)

    def test_05_location_usage_change_recomputes_priority(self):
        """PRIORITY-001: schimbarea tipului locatiei recalculeaza prioritatea."""
        quant = (
            self.env["stock.quant"]
            .sudo()
            .create({"product_id": self.product.id, "location_id": self.loc_3.id, "quantity": 0})
        )
        self.assertEqual(self._read_priority(quant), 7)

        self.loc_3.usage = "transit"
        self.assertEqual(self._read_priority(quant), 999)

    def test_06_archive_rule_recomputes_priority(self):
        """PRIORITY-002: arhivarea / reactivarea regulii recalculeaza prioritatea."""
        rule = self.env["stock.putaway.rule"].search(
            [("product_id", "=", self.product.id), ("location_out_id", "=", self.loc_2.id)]
        )
        quant = self._make_quant(self.loc_2)
        self.assertEqual(self._read_priority(quant), 5)

        rule.active = False
        self.assertEqual(self._read_priority(quant), 999)

        rule.active = True
        self.assertEqual(self._read_priority(quant), 5)

    def test_07_default_priority_param_change(self):
        """PRIORITY-001: schimbarea prioritatii implicite recalculeaza cuantele fara regula."""
        loc_4 = self.env["stock.location"].create({"name": "Loc 4", "location_id": self.stock_location.id})
        quant_default = self._make_quant(loc_4)
        quant_rule = self._make_quant(self.loc_2)
        self.assertEqual(self._read_priority(quant_default), 999)

        icp = self.env["ir.config_parameter"].sudo()
        icp.set_int("stock.removal_priority.default", 500)
        self.assertEqual(self._read_priority(quant_default), 500)
        self.assertEqual(self._read_priority(quant_rule), 5)

        icp.set_str("stock.removal_priority.default", False)
        self.assertEqual(self._read_priority(quant_default), 999)
