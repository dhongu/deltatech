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
