from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class TestMrpProduction(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Creare categorie de produs cu cost_categ setat
        cls.category = cls.env["product.category"].create({"name": "Test Category", "cost_categ": "raw"})

        # Creare produs finit
        cls.finished_product = cls.env["product.product"].create(
            {"name": "Finished Product", "is_storable": True, "categ_id": cls.category.id}
        )

        # Creare componentă
        cls.component = cls.env["product.product"].create(
            {"name": "Component", "is_storable": True, "categ_id": cls.category.id, "standard_price": 10.0}
        )

        # Creare Bill of Materials (BoM)
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished_product.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [(0, 0, {"product_id": cls.component.id, "product_qty": 2.0})],
            }
        )

    def test_mrp_production_cost_detail(self):
        # Creare comandă de producție
        production = self.env["mrp.production"].create(
            {
                "product_id": self.finished_product.id,
                "bom_id": self.bom.id,
                "product_qty": 1.0,
            }
        )
        production.action_confirm()

        # Verificăm dacă s-au generat detalii de cost (ar trebui să fie goale până la finalizare)
        production._compute_cost_detail()
        self.assertEqual(len(production.cost_detail_ids), 0)

        # Notă: Deoarece deltatech.cost.detail este un view SQL care depinde de valoarea (stock_move.value)
        # mișcărilor în starea 'done', un test complet ar necesita simularea fluxului de stoc.
        # Pentru acest test, verificăm măcar dacă metoda de calcul poate fi apelată fără erori.
        production.recompute_cost_detail()


@tagged("post_install", "-at_install")
class TestMrpProductionCostValue(TransactionCase):
    """The cost detail view and the cost analysis report keep the 19.0 semantics:
    consumed values are positive even if stock.move.value is signed in 20.0."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.raw_categ = cls.env["product.category"].create({"name": "Cost raw", "cost_categ": "raw"})
        cls.pak_categ = cls.env["product.category"].create({"name": "Cost pak", "cost_categ": "pak"})
        cls.finished_product = cls.env["product.product"].create(
            {"name": "Cost finished", "is_storable": True, "categ_id": cls.raw_categ.id}
        )
        cls.component = cls.env["product.product"].create(
            {"name": "Cost component", "is_storable": True, "categ_id": cls.raw_categ.id, "standard_price": 10.0}
        )
        cls.packing = cls.env["product.product"].create(
            {"name": "Cost packing", "is_storable": True, "categ_id": cls.pak_categ.id, "standard_price": 3.0}
        )
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished_product.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [
                    Command.create({"product_id": cls.component.id, "product_qty": 2.0}),
                    Command.create({"product_id": cls.packing.id, "product_qty": 1.0}),
                ],
            }
        )

    def _produce(self):
        production = self.env["mrp.production"].create(
            {"product_id": self.finished_product.id, "bom_id": self.bom.id, "product_qty": 1.0}
        )
        production.action_confirm()
        production.qty_producing = 1.0
        production._set_qty_producing()
        production.move_raw_ids.picked = True
        production.button_mark_done()
        self.assertEqual(production.state, "done")
        self.env.flush_all()
        return production

    def test_cost_detail_positive_amounts(self):
        production = self._produce()
        production.recompute_cost_detail()
        amounts = {detail.cost_categ: detail.amount for detail in production.cost_detail_ids}
        self.assertAlmostEqual(amounts.get("raw"), 20.0)
        self.assertAlmostEqual(amounts.get("pak"), 3.0)

    def test_mrp_report_consumed_values(self):
        production = self._produce()
        line = self.env["deltatech.mrp.report"].search([("production_id", "=", production.id)])
        self.assertEqual(len(line), 1)
        self.assertEqual(line.product_uom, self.finished_product.uom_id)
        self.assertAlmostEqual(line.consumed_val, 23.0)
        self.assertAlmostEqual(line.consumed_raw_val, 20.0)
        self.assertAlmostEqual(line.consumed_pak_val, 3.0)
        self.assertGreaterEqual(line.product_val_ef, 0.0)
