# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestDCReportIssues(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "DC Company B"})
        cls.env.user.company_ids |= cls.company_b
        cls.product = cls.env["product.product"].create(
            {"name": "DC Lot Product", "type": "consu", "is_storable": True, "tracking": "lot"}
        )
        cls.product_simple = cls.env["product.product"].create(
            {"name": "DC Simple Product", "type": "consu", "is_storable": True}
        )

    def _env_ab(self):
        """Environment with companies A and B allowed and A current."""
        return self.env(context=dict(self.env.context, allowed_company_ids=[self.company_a.id, self.company_b.id]))

    # Issue #3382 -------------------------------------------------------

    def test_lot_report_without_production_date(self):
        lot = self.env["stock.lot"].create({"name": "DC-NODATE", "product_id": self.product.id})
        self.assertFalse(lot.production_date)
        values = self.env["report.deltatech_dc.report_dc_lot"]._get_report_values(lot.ids)
        dc = values["docs"]
        self.assertEqual(len(dc), 1)
        self.assertEqual(dc.lot_id, lot)
        self.assertEqual(dc.date, fields.Date.context_today(dc))

    def test_invoice_report_lot_without_production_date(self):
        lot = self.env["stock.lot"].create({"name": "DC-INV-NODATE", "product_id": self.product.id})
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.env["res.partner"].create({"name": "DC Partner"}).id,
                "invoice_line_ids": [(0, 0, {"product_id": self.product.id, "quantity": 1, "price_unit": 10})],
            }
        )
        invoice.action_post()
        with patch.object(
            type(self.env["account.move"]), "_get_invoiced_lot_values", lambda self: [{"lot_id": lot.id}]
        ):
            values = self.env["report.deltatech_dc.report_dc_invoice"]._get_report_values(invoice.ids)
        dc = values["docs"].filtered(lambda d: d.lot_id == lot)
        self.assertEqual(len(dc), 1)
        self.assertEqual(dc.date, fields.Date.context_today(dc))

    # Issue #3383 -------------------------------------------------------

    def test_lot_report_uses_lot_company(self):
        env = self._env_ab()
        lot = env["stock.lot"].create(
            {
                "name": "DC-B",
                "product_id": self.product.id,
                "company_id": self.company_b.id,
                "production_date": "2021-01-01",
            }
        )
        self.assertEqual(env.company, self.company_a)
        dc = env["report.deltatech_dc.report_dc_lot"]._get_report_values(lot.ids)["docs"]
        self.assertEqual(dc.company_id, self.company_b)

    def test_picking_report_does_not_reuse_other_company_declaration(self):
        env = self._env_ab()
        warehouse_b = env["stock.warehouse"].search([("company_id", "=", self.company_b.id)], limit=1)
        picking = (
            env["stock.picking"]
            .with_company(self.company_b)
            .create(
                {
                    "picking_type_id": warehouse_b.out_type_id.id,
                    "company_id": self.company_b.id,
                    "move_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product_simple.id,
                                "product_uom_qty": 1,
                                "product_uom": self.product_simple.uom_id.id,
                            },
                        )
                    ],
                }
            )
        )
        picking.action_confirm()
        picking.move_ids.quantity = 1
        picking.move_ids.picked = True
        picking._action_done()
        # a company A declaration for the same product and date already exists
        env["deltatech.dc"].create(
            {
                "product_id": self.product_simple.id,
                "date": picking.date_done,
                "company_id": self.company_a.id,
            }
        )
        dc = env["report.deltatech_dc.report_dc_picking"]._get_report_values(picking.ids)["docs"]
        self.assertTrue(dc)
        self.assertEqual(dc.company_id, self.company_b)

    def test_report_prints_declaration_company_as_issuer(self):
        env = self._env_ab()
        dc = env["deltatech.dc"].create({"product_id": self.product_simple.id, "company_id": self.company_b.id})
        html, _ = env["ir.actions.report"]._render_qweb_html("deltatech_dc.report_dc", dc.ids)
        html = html.decode()
        declaration = html[html.index('id="declaration"') : html.index('id="signature"')]
        self.assertIn("DC Company B", declaration)
        self.assertNotIn(self.company_a.name, declaration)
