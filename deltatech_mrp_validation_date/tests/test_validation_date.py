from odoo import fields
from odoo.tests.common import TransactionCase


class TestMrpValidationDate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Produs finit + componentă (depozitabile)
        cls.finished_product = cls.env["product.product"].create({"name": "Finished Product", "is_storable": True})
        cls.component = cls.env["product.product"].create(
            {"name": "Component", "is_storable": True, "standard_price": 10.0}
        )

        # Listă de materiale
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished_product.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [(0, 0, {"product_id": cls.component.id, "product_qty": 2.0})],
            }
        )

    def _create_production(self):
        production = self.env["mrp.production"].create(
            {
                "product_id": self.finished_product.id,
                "bom_id": self.bom.id,
                "product_qty": 1.0,
            }
        )
        production.action_confirm()
        return production

    def test_validation_date_set_on_mark_done(self):
        """La finalizare (button_mark_done) data de validare devine ziua curentă."""
        production = self._create_production()
        self.assertFalse(production.validation_date)

        production.qty_producing = production.product_qty
        production.with_context(skip_consumption=True).button_mark_done()

        self.assertEqual(production.state, "done")
        self.assertEqual(production.validation_date, fields.Date.context_today(production))

    def test_validation_date_empty_before_done(self):
        """Cât timp comanda nu e finalizată, data de validare rămâne goală."""
        production = self._create_production()
        self.assertFalse(production.validation_date)
        self.assertNotEqual(production.state, "done")
