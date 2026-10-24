from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestMrpBomAlternative(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_kg = cls.env.ref("uom.product_uom_kgm")
        cls.uom_gram = cls.env.ref("uom.product_uom_gram")
        cls.env.company.mrp_alternative_partial = True
        cls.env.company.mrp_alternative_on_assign = True

        product = cls.env["product.product"]
        cls.finished = product.create({"name": "Finished", "is_storable": True})
        cls.component = product.create({"name": "Component A", "is_storable": True})
        cls.alt_b = product.create({"name": "Alternative B", "is_storable": True})
        cls.alt_c = product.create({"name": "Alternative C", "is_storable": True})
        cls.resin = product.create({"name": "Resin", "is_storable": True, "uom_id": cls.uom_kg.id})
        cls.resin_alt = product.create({"name": "Resin Alt", "is_storable": True, "uom_id": cls.uom_gram.id})

        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [
                    (0, 0, {"product_id": cls.component.id, "product_qty": 1.0, "alternative_policy": "auto"}),
                    (0, 0, {"product_id": cls.resin.id, "product_qty": 1.0, "uom_id": cls.uom_kg.id}),
                ],
            }
        )
        cls.line_a = cls.bom.bom_line_ids.filtered(lambda line: line.product_id == cls.component)
        cls.line_resin = cls.bom.bom_line_ids - cls.line_a
        # 1 A = 2 B ; 1 A = 1 C (second choice)
        cls.alternative_b = cls.env["mrp.bom.line.alternative"].create(
            {"bom_line_id": cls.line_a.id, "product_id": cls.alt_b.id, "product_qty": 2.0, "sequence": 1}
        )
        cls.alternative_c = cls.env["mrp.bom.line.alternative"].create(
            {"bom_line_id": cls.line_a.id, "product_id": cls.alt_c.id, "product_qty": 1.0, "sequence": 2}
        )
        # 1 kg resin = 1200 g resin alt
        cls.alternative_resin = cls.env["mrp.bom.line.alternative"].create(
            {"bom_line_id": cls.line_resin.id, "product_id": cls.resin_alt.id, "product_qty": 1200.0}
        )

    def _stock(self, product, qty):
        self.env["stock.quant"]._update_available_quantity(product, self.stock_location, qty)

    def _create_production(self, qty=10.0):
        return self.env["mrp.production"].create(
            {"product_id": self.finished.id, "bom_id": self.bom.id, "product_qty": qty}
        )

    def _moves(self, production, product):
        return production.move_raw_ids.filtered(lambda m: m.product_id == product and m.state != "cancel")

    def test_01_auto_partial_on_confirm(self):
        self._stock(self.component, 3)
        self._stock(self.alt_b, 100)
        self._stock(self.resin, 100)
        production = self._create_production(10)
        production.action_confirm()

        self.assertEqual(self._moves(production, self.component).product_uom_qty, 3)
        alt_move = self._moves(production, self.alt_b)
        self.assertEqual(alt_move.product_uom_qty, 14)
        self.assertEqual(alt_move.original_product_id, self.component)
        self.assertEqual(alt_move.bom_line_id, self.line_a)
        self.assertEqual(alt_move.substitution_reason, "auto")
        self.assertEqual(alt_move.state, "assigned")
        self.assertFalse(self._moves(production, self.alt_c))

    def test_02_auto_split_between_alternatives(self):
        self._stock(self.alt_b, 8)  # covers 4 A
        self._stock(self.alt_c, 100)
        production = self._create_production(10)
        production.action_confirm()

        self.assertFalse(self._moves(production, self.component))
        self.assertEqual(self._moves(production, self.alt_b).product_uom_qty, 8)
        self.assertEqual(self._moves(production, self.alt_c).product_uom_qty, 6)

    def test_03_no_partial_uses_alternative_covering_all(self):
        self.env.company.mrp_alternative_partial = False
        self._stock(self.component, 3)
        self._stock(self.alt_b, 8)  # 4 A, not enough for the 7 missing
        self._stock(self.alt_c, 100)
        production = self._create_production(10)
        production.action_confirm()

        self.assertEqual(self._moves(production, self.component).product_uom_qty, 3)
        self.assertFalse(self._moves(production, self.alt_b))
        self.assertEqual(self._moves(production, self.alt_c).product_uom_qty, 7)

    def test_04_expired_alternative_ignored(self):
        self.alternative_b.date_end = fields.Date.today() - timedelta(days=1)
        self._stock(self.alt_b, 100)
        self._stock(self.alt_c, 100)
        production = self._create_production(5)
        production.action_confirm()

        self.assertFalse(self._moves(production, self.alt_b))
        self.assertEqual(self._moves(production, self.alt_c).product_uom_qty, 5)

    def test_05_manual_policy_not_automatic(self):
        self._stock(self.resin_alt, 100000)
        production = self._create_production(5)
        production.action_confirm()
        self.assertEqual(self._moves(production, self.resin).product_uom_qty, 5)
        self.assertFalse(self._moves(production, self.resin_alt))

    def test_06_substitute_on_availability_check(self):
        production = self._create_production(5)
        production.action_confirm()
        self.assertEqual(self._moves(production, self.component).product_uom_qty, 5)
        self._stock(self.alt_c, 100)
        production.action_assign()
        self.assertFalse(self._moves(production, self.component))
        self.assertEqual(self._moves(production, self.alt_c).product_uom_qty, 5)

    def test_07_manual_wizard_other_uom(self):
        self._stock(self.resin, 5)
        self._stock(self.resin_alt, 10000)
        production = self._create_production(5)
        production.action_confirm()
        resin_move = self._moves(production, self.resin)
        self.assertEqual(resin_move.quantity, 5)

        action = resin_move.action_open_bom_alternative_substitute()
        wizard_form = Form(self.env["mrp.bom.alternative.substitute"].with_context(**action["context"]))
        wizard_form.alternative_id = self.alternative_resin
        wizard_form.qty = 2
        wizard = wizard_form.save()
        self.assertEqual(wizard.alternative_qty, 2400)
        wizard.action_substitute()

        self.assertEqual(resin_move.product_uom_qty, 3)
        self.assertEqual(resin_move.quantity, 3)
        alt_move = self._moves(production, self.resin_alt)
        self.assertEqual(alt_move.product_uom_qty, 2400)
        self.assertEqual(alt_move.uom_id, self.uom_gram)
        self.assertEqual(alt_move.substitution_reason, "manual")

    def test_08_wizard_rejects_too_much(self):
        self._stock(self.resin_alt, 10000)
        production = self._create_production(2)
        production.action_confirm()
        resin_move = self._moves(production, self.resin)
        wizard = self.env["mrp.bom.alternative.substitute"].create(
            {"move_id": resin_move.id, "alternative_id": self.alternative_resin.id, "qty": 3}
        )
        with self.assertRaises(UserError):
            wizard.action_substitute()

    def test_09_no_consumption_warning_after_substitution(self):
        self._stock(self.component, 3)
        self._stock(self.alt_b, 100)
        self._stock(self.resin, 100)
        production = self._create_production(10)
        production.action_confirm()
        production.qty_producing = 10
        production._set_qty_producing()
        production.move_raw_ids.picked = True
        self.assertFalse(production._get_consumption_issues())
        production.button_mark_done()
        self.assertEqual(production.state, "done")

    def test_10_change_production_qty_scales_alternative(self):
        self._stock(self.alt_b, 100)
        self._stock(self.resin, 100)
        production = self._create_production(4)
        production.action_confirm()
        self.assertEqual(self._moves(production, self.alt_b).product_uom_qty, 8)
        self.env["change.production.qty"].create({"mo_id": production.id, "product_qty": 6}).change_prod_qty()
        self.assertEqual(self._moves(production, self.alt_b).product_uom_qty, 12)

    def test_11_constraints(self):
        with self.assertRaises(ValidationError):
            self.env["mrp.bom.line.alternative"].create(
                {"bom_line_id": self.line_a.id, "product_id": self.component.id}
            )
        with self.assertRaises(ValidationError):
            self.env["mrp.bom.line.alternative"].create(
                {"bom_line_id": self.line_a.id, "product_id": self.alt_c.id, "product_qty": 0}
            )
