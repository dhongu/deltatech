# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase
from odoo.tools import html2plaintext


@tagged("post_install", "-at_install")
class TestDC(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_a = self.env["res.partner"].create({"name": "Test Partner"})
        self.product_storable = self.env["product.product"].create(
            {
                "name": "Storable Product",
                "type": "consu",
                "is_storable": True,
            }
        )
        self.product_service = self.env["product.product"].create(
            {
                "name": "Service Product",
                "type": "service",
            }
        )
        self.product_with_lot = self.env["product.product"].create(
            {
                "name": "Product with Lot",
                "type": "consu",
                "is_storable": True,
            }
        )

    def test_create_dc(self):
        form_dc = Form(self.env["deltatech.dc"])
        form_dc.name = "Test"
        form_dc.date = "2021-01-01"
        form_dc.product_id = self.product_storable
        form_dc.save()

    def test_lot(self):
        form_lot = Form(self.env["stock.lot"])
        form_lot.name = "Test"
        form_lot.product_id = self.product_storable
        lot = form_lot.save()
        lot.production_date = "2021-01-01"
        dates = lot._get_dates(product_id=self.product_storable.id)
        self.assertEqual(set(dates), {"expiration_date", "use_date", "removal_date", "alert_date"})

    def test_invoice_report_dc_with_storable_products(self):
        """Test raport DC factură include produse stocabile (consu) și exclude servicii."""
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_storable.id,
                            "quantity": 2,
                            "price_unit": 100,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_service.id,
                            "quantity": 1,
                            "price_unit": 50,
                        },
                    ),
                ],
            }
        )
        invoice.action_post()

        report = self.env["report.deltatech_dc.report_dc_invoice"]
        values = report._get_report_values(invoice.ids)

        dc_products = set(dc.product_id.id for dc in values["docs"])
        self.assertIn(
            self.product_storable.id,
            dc_products,
            "DC raport trebuie să includă produse stocabile",
        )
        self.assertNotIn(
            self.product_service.id,
            dc_products,
            "DC raport nu trebuie să includă servicii",
        )

    def test_invoice_report_dc_with_lot(self):
        """Test raport DC factură cu produse cu trasabilitate (lot)."""
        self.env["stock.lot"].create(
            {
                "name": "LOT001",
                "product_id": self.product_with_lot.id,
                "production_date": "2021-01-01",
            }
        )

        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_a.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_with_lot.id,
                            "quantity": 1,
                            "price_unit": 100,
                        },
                    ),
                ],
            }
        )

        self.env["account.move.line"].search(
            [("move_id", "=", invoice.id), ("product_id", "=", self.product_with_lot.id)]
        ).quantity = 1

        invoice.action_post()

        report = self.env["report.deltatech_dc.report_dc_invoice"]
        values = report._get_report_values(invoice.ids)

        self.assertGreater(len(values["docs"]), 0, "DC raport trebuie să conțină declarații")

    def test_picking_report_dc_without_lot(self):
        """Test raport DC picking include produse fără lot (consum)."""
        warehouse = self.env["stock.warehouse"].search([], limit=1)
        if not warehouse:
            warehouse = self.env["stock.warehouse"].create(
                {
                    "name": "Test Warehouse",
                    "code": "TEST",
                }
            )

        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": warehouse.out_type_id.id,
                "partner_id": self.partner_a.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_storable.id,
                            "product_uom_qty": 1,
                            "uom_id": self.product_storable.uom_id.id,
                        },
                    ),
                ],
            }
        )

        picking.button_validate()

        report = self.env["report.deltatech_dc.report_dc_picking"]
        values = report._get_report_values(picking.ids)

        self.assertGreater(
            len(values["docs"]),
            0,
            "DC raport picking trebuie să includă produse fără lot",
        )

    def _render_html(self, report_ref, records):
        html = self.env["ir.actions.report"]._render_qweb_html(report_ref, records.ids)[0]
        return html2plaintext(html)

    def test_create_dc_sequence_and_display_name(self):
        """Numărul declarației vine din secvența `declaration.conformity`."""
        dc = self.env["deltatech.dc"].create(
            {"name": "New", "product_id": self.product_storable.id, "date": "2021-01-01"}
        )
        self.assertTrue(dc.name.startswith("DC/"))
        self.assertIn(dc.name, dc.display_name)
        self.assertEqual(dc.company_id, self.env.company)

    def test_render_report_dc(self):
        """Raportul principal se randează cu standardele produsului."""
        self.product_storable.write(
            {
                "company_standard": "SF-001",
                "data_sheet": 12,
                "technical_specification": 34,
                "standards": "SR EN 123",
            }
        )
        dc = self.env["deltatech.dc"].create(
            {"name": "DC-TEST", "product_id": self.product_storable.id, "date": "2021-01-01"}
        )
        text = self._render_html("deltatech_dc.action_report_dc", dc)
        self.assertIn("DC-TEST", text)
        self.assertIn("Storable Product", text)
        self.assertIn("SF-001", text)
        self.assertIn("SR EN 123", text)

    def test_render_report_dc_lot(self):
        """Raportul pe lot creează (o singură dată) declarația lotului și o randează."""
        lot = self.env["stock.lot"].create(
            {
                "name": "LOT-RENDER",
                "product_id": self.product_with_lot.id,
                "production_date": "2021-01-01",
            }
        )
        text = self._render_html("deltatech_dc.action_report_dc_lot", lot)
        self.assertIn("LOT-RENDER", text)
        dc = self.env["deltatech.dc"].search([("lot_id", "=", lot.id)])
        self.assertEqual(len(dc), 1)
        self._render_html("deltatech_dc.action_report_dc_lot", lot)
        self.assertEqual(self.env["deltatech.dc"].search_count([("lot_id", "=", lot.id)]), 1)

    def test_invoice_report_dc_with_invoiced_lots(self):
        """Factura dintr-o comandă livrată pe lot: `_get_invoiced_lot_values()` dă lotul,
        iar raportul generează declarația pe lot (nu pe produs/dată)."""
        if "picking_ids" not in self.env["sale.order"]._fields:
            self.skipTest("necesită sale_stock (livrarea comenzii), care nu e dependență a modulului")
        self.product_with_lot.write({"tracking": "lot", "invoice_policy": "delivery"})
        warehouse = self.env["stock.warehouse"].search([("company_id", "=", self.env.company.id)], limit=1)
        lot = self.env["stock.lot"].create(
            {"name": "LOT-INV", "product_id": self.product_with_lot.id, "production_date": "2021-01-01"}
        )
        self.env["stock.quant"]._update_available_quantity(self.product_with_lot, warehouse.lot_stock_id, 5, lot_id=lot)
        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner_a.id,
                "order_line": [(0, 0, {"product_id": self.product_with_lot.id, "product_uom_qty": 2})],
            }
        )
        so.action_confirm()
        picking = so.picking_ids
        picking.move_ids.write({"quantity": 2, "picked": True})
        picking.button_validate()
        self.assertEqual(picking.move_line_ids.lot_id, lot)

        invoice = so._create_invoices()
        invoice.action_post()
        lot_values = invoice._get_invoiced_lot_values()
        self.assertEqual([v["lot_id"] for v in lot_values], [lot.id])

        values = self.env["report.deltatech_dc.report_dc_invoice"]._get_report_values(invoice.ids)
        self.assertEqual(values["docs"].lot_id, lot)
        self.assertEqual(values["docs"].product_id, self.product_with_lot)

        text = self._render_html("deltatech_dc.action_report_dc_invoice", invoice)
        self.assertIn("LOT-INV", text)

        # pe livrare: aceeași declarație pe lot, refolosită
        values = self.env["report.deltatech_dc.report_dc_picking"]._get_report_values(picking.ids)
        self.assertEqual(values["docs"].lot_id, lot)
        text = self._render_html("deltatech_dc.action_report_dc_picking_form_2", picking)
        self.assertIn("LOT-INV", text)
        self.assertIn("Product with Lot", text)
