# ©  2015-2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestStockQuantReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search([], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id

        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
                "list_price": 100.0,
            }
        )

        # Adăugăm stoc
        cls.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": cls.product.id,
                "location_id": cls.stock_location.id,
                "inventory_quantity": 10.0,
            }
        ).action_apply_inventory()

        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test Pricelist",
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "compute_price": "formula",
                            "base": "list_price",
                            "price_discount": 10.0,  # 10% reducere
                        },
                    )
                ],
            }
        )
        cls.partner.property_product_pricelist = cls.pricelist

    def test_01_stock_quant_report_basic(self):
        """Test basic report generation"""
        report_wizard = self.env["stock.quant.report"].create(
            {
                "location_id": self.stock_location.id,
                "partner_id": self.partner.id,
                "show_thresholds": False,
            }
        )
        report_wizard.onchange_partner_id()
        self.assertEqual(report_wizard.pricelist_id, self.pricelist)

        report_wizard.compute_data_for_report()

        report_lines = self.env["stock.quant.report.value"].search([("report_id", "=", report_wizard.id)])
        self.assertTrue(report_lines)
        product_line = report_lines.filtered(lambda l: l.product_id == self.product)
        self.assertEqual(product_line.qty, 10.0)
        self.assertEqual(product_line.list_price, 100.0)
        self.assertEqual(product_line.price_reseller, 90.0)

    def test_02_stock_quant_report_thresholds(self):
        """Test report generation with thresholds"""
        report_wizard = self.env["stock.quant.report"].create(
            {
                "location_id": self.stock_location.id,
                "partner_id": self.partner.id,
                "show_thresholds": True,
                "stock_threshold_1": 5.0,
                "stock_threshold_1_text": "Low",
                "stock_threshold_2": 20.0,
                "stock_threshold_2_text": "Medium",
                "stock_no_threshold_text": "High",
            }
        )
        report_wizard.onchange_partner_id()
        report_wizard.compute_data_for_report()

        report_lines = self.env["stock.quant.report.value"].search([("report_id", "=", report_wizard.id)])
        product_line = report_lines.filtered(lambda l: l.product_id == self.product)
        # Cantitatea este 10.0, deci ar trebui să fie "Medium" (între 5 și 20)
        self.assertEqual(product_line.qty_text, "Medium")

        # Testăm pentru High (peste 20)
        self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": self.product.id,
                "location_id": self.stock_location.id,
                "inventory_quantity": 25.0,
            }
        ).action_apply_inventory()

        report_wizard_high = self.env["stock.quant.report"].create(
            {
                "location_id": self.stock_location.id,
                "partner_id": self.partner.id,
                "show_thresholds": True,
                "stock_threshold_1": 5.0,
                "stock_threshold_1_text": "Low",
                "stock_threshold_2": 20.0,
                "stock_threshold_2_text": "Medium",
                "stock_no_threshold_text": "High",
            }
        )
        report_wizard_high.onchange_partner_id()
        report_wizard_high.compute_data_for_report()
        report_lines_high = self.env["stock.quant.report.value"].search([("report_id", "=", report_wizard_high.id)])
        product_line_high = report_lines_high.filtered(lambda l: l.product_id == self.product)
        self.assertEqual(product_line_high.qty_text, "High")

    def test_03_stock_quant_report_execute(self):
        """Test the do_execute method"""
        report_wizard = self.env["stock.quant.report"].create(
            {
                "location_id": self.stock_location.id,
                "refresh_report": True,
            }
        )
        action = report_wizard.do_execute()
        self.assertEqual(action["res_model"], "stock.quant.report.value")

        # Rulăm din nou cu refresh_report=True
        report_wizard_2 = self.env["stock.quant.report"].create(
            {
                "location_id": self.stock_location.id,
                "refresh_report": True,
            }
        )
        report_wizard_2.do_execute()
        # Ar trebui să rămână doar unul (cel nou creat sau cel vechi șters)
        remaining_reports = self.env["stock.quant.report"].search([("location_id", "=", self.stock_location.id)])
        self.assertIn(report_wizard_2.id, remaining_reports.ids)

    def _create_report(self, **vals):
        values = {
            "location_id": self.stock_location.id,
            "partner_id": self.partner.id,
            "pricelist_id": self.pricelist.id,
            "refresh_report": False,
        }
        values.update(vals)
        return self.env["stock.quant.report"].create(values)

    def test_04_cache_not_reused_for_other_configuration(self):
        """RESELLER-001: a cached report is reused only for the same configuration"""
        report_a = self._create_report(refresh_report=True)
        action = report_a.do_execute()
        self.assertEqual(action["domain"], [("report_id", "=", report_a.id)])

        # Same settings: the cached report is reused
        report_same = self._create_report()
        action = report_same.do_execute()
        self.assertEqual(action["domain"], [("report_id", "=", report_a.id)])

        partner_b = self.env["res.partner"].create({"name": "Test Partner B"})
        pricelist_b = self.env["product.pricelist"].create(
            {
                "name": "Test Pricelist B",
                "item_ids": [
                    (0, 0, {"compute_price": "formula", "base": "list_price", "price_discount": 20.0}),
                ],
            }
        )
        report_b = self._create_report(partner_id=partner_b.id, pricelist_id=pricelist_b.id)
        action = report_b.do_execute()
        self.assertEqual(action["domain"], [("report_id", "=", report_b.id)])
        line = report_b.lines_ids.filtered(lambda l: l.product_id == self.product)
        self.assertEqual(line.price_reseller, 80.0)

        report_thr = self._create_report(show_thresholds=True, stock_threshold_2_text="Medium")
        action = report_thr.do_execute()
        self.assertEqual(action["domain"], [("report_id", "=", report_thr.id)])
        line = report_thr.lines_ids.filtered(lambda l: l.product_id == self.product)
        self.assertEqual(line.qty_text, "Medium")

        # Refreshing one configuration keeps the reports of the other configurations
        self._create_report(refresh_report=True).do_execute()
        self.assertTrue(report_b.exists())
        self.assertTrue(report_thr.exists())
        self.assertFalse(report_a.exists())
