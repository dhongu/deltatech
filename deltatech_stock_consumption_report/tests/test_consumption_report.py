from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.stock_account.tests.test_stockvaluation import TestStockValuationCommon


@tagged("post_install", "-at_install")
class TestConsumptionReport(TestStockValuationCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # fara localizarea romana nu exista tipul de locatie "consume"
        cls.classPatch(
            type(cls.env["stock.location"]),
            "_get_consumption_usages",
            lambda self: ["production"],
        )
        cls.consume_location = cls.env["stock.location"].create(
            {
                "name": "Consum test",
                "usage": "production",
                "company_id": cls.env.company.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Consumabil test", "is_storable": True, "standard_price": 10.0}
        )
        cls.env["stock.quant"]._update_available_quantity(cls.product, cls.stock_location, 20.0)
        cls.purpose = cls.env["stock.consumption.purpose"].create({"name": "Investitii"})
        cls.picking_type = cls.env["stock.picking.type"].create(
            {
                "name": "Consum test",
                "code": "internal",
                "sequence_code": "CT",
                "warehouse_id": cls.warehouse.id,
                "default_location_src_id": cls.stock_location.id,
                "default_location_dest_id": cls.consume_location.id,
            }
        )
        picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.picking_type.id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.consume_location.id,
                "consumption_purpose_id": cls.purpose.id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 5.0,
                            "quantity": 5.0,
                            "location_id": cls.stock_location.id,
                            "location_dest_id": cls.consume_location.id,
                        }
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.button_validate()
        cls.picking = picking
        cls.move = picking.move_ids

    def _wizard(self):
        today = fields.Date.context_today(self.env.user)
        return self.env["stock.consumption.report.wizard"].create(
            {
                "date_from": today.replace(day=1),
                "date_to": today,
                "picking_type_ids": [Command.set(self.picking_type.ids)],
            }
        )

    def test_report_data(self):
        summary, detail = self._wizard()._get_report_data()
        self.assertEqual(len(detail), 1)
        self.assertEqual(detail[0]["quantity"], 5.0)
        self.assertAlmostEqual(detail[0]["value"], self.move.value)
        self.assertEqual(detail[0]["purpose"], "Investitii")
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["purpose"], "Investitii")
        self.assertAlmostEqual(summary[0]["value"], self.move.value)

    def test_report_without_purpose(self):
        self.picking.consumption_purpose_id = False
        summary, detail = self._wizard()._get_report_data()
        self.assertEqual(summary[0]["purpose"], "Undefined")
        self.assertEqual(detail[0]["purpose"], "Undefined")

    def test_return_keeps_purpose(self):
        wizard = (
            self.env["stock.return.picking"]
            .with_context(active_id=self.picking.id, active_model="stock.picking")
            .create({})
        )
        wizard.product_return_moves.quantity = 1.0
        action = wizard.action_create_returns()
        return_picking = self.env["stock.picking"].browse(action["res_id"])
        self.assertEqual(return_picking.consumption_purpose_id, self.purpose)

    def test_export_and_view(self):
        wizard = self._wizard()
        wizard.action_export_xlsx()
        self.assertTrue(wizard.file_data)
        action = wizard.action_view()
        lines = self.env[action["res_model"]].search(action["domain"])
        self.assertEqual(lines.product_id, self.product)
        self.assertAlmostEqual(lines.value, self.move.value)

    def test_value_from_journal_entry(self):
        """Cu nota contabila, valoarea vine din creditul liniilor produsului, nu din miscare."""
        product = self.product_avco_auto
        self._make_in_move(product, 10, 8.0)
        self.consume_location.valuation_account_id = self.account_expense
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.picking_type.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.consume_location.id,
                "consumption_purpose_id": self.purpose.id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_uom_qty": 3.0,
                            "quantity": 3.0,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.consume_location.id,
                        }
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.button_validate()
        move = picking.move_ids
        self.assertTrue(move.account_move_id, "consumul nu a generat nota contabila")
        stock_lines = move.account_move_id.line_ids.filtered(
            lambda aml: aml.account_id == product._get_product_accounts()["stock_valuation"]
        )
        entry_value = -sum(stock_lines.mapped("balance"))
        self.assertAlmostEqual(entry_value, 24.0)
        # valoarea miscarii diferita de nota: raportul ramane pe nota
        move.value = 999.0
        values = self._wizard()._get_move_values(move | self.move)
        self.assertAlmostEqual(values[move.id], 24.0)
        # bonul fara nota contabila ramane pe valoarea miscarii
        self.assertAlmostEqual(values[self.move.id], self.move.value)
