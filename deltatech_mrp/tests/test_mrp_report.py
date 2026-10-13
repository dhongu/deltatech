from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMrpReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        valuation = {"property_cost_method": "average", "property_valuation": "real_time"}
        cls.categ_raw = cls.env["product.category"].create(dict(valuation, name="Raw", cost_categ="raw"))
        cls.categ_pak = cls.env["product.category"].create(dict(valuation, name="Packing", cost_categ="pak"))
        cls.categ_semi = cls.env["product.category"].create(dict(valuation, name="Semi", cost_categ="semi"))
        cls.finished = cls.env["product.product"].create(
            {"name": "Report Finished", "is_storable": True, "categ_id": cls.categ_semi.id}
        )
        cls.raw = cls.env["product.product"].create(
            {"name": "Report Raw", "is_storable": True, "categ_id": cls.categ_raw.id, "standard_price": 3.0}
        )
        cls.pak = cls.env["product.product"].create(
            {"name": "Report Box", "is_storable": True, "categ_id": cls.categ_pak.id, "standard_price": 1.0}
        )
        stock_location = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        for product in cls.raw | cls.pak:
            cls.env["stock.quant"].create(
                {"product_id": product.id, "location_id": stock_location.lot_stock_id.id, "inventory_quantity": 100}
            ).action_apply_inventory()
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished.product_tmpl_id.id,
                "product_qty": 1.0,
                "bom_line_ids": [
                    (0, 0, {"product_id": cls.raw.id, "product_qty": 2.0}),
                    (0, 0, {"product_id": cls.pak.id, "product_qty": 1.0}),
                ],
            }
        )

    def test_report_totals_with_several_cost_categories(self):
        """MRP-001: consumption in two cost categories must not multiply the production totals"""
        production = self.env["mrp.production"].create(
            {"product_id": self.finished.id, "bom_id": self.bom.id, "product_qty": 10.0}
        )
        production.action_confirm()
        production.qty_producing = 10.0
        production.move_raw_ids.picked = True
        production.button_mark_done()
        self.assertEqual(production.state, "done")
        self.env.flush_all()

        line = self.env["deltatech.mrp.report"].search([("production_id", "=", production.id)])
        self.assertEqual(len(line), 1)
        self.assertAlmostEqual(line.product_qty, 10.0)
        self.assertAlmostEqual(line.product_qty_ef, 10.0)
        self.assertAlmostEqual(line.consumed_raw_val, 60.0)
        self.assertAlmostEqual(line.consumed_pak_val, 10.0)
        self.assertAlmostEqual(line.consumed_val, 70.0)
        self.assertAlmostEqual(line.product_val_ef, sum(production.move_finished_ids.mapped("value")))
