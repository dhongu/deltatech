# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


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
        lot._get_dates(product_id=self.product_storable.id)

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
                            "product_uom": self.product_storable.uom_id.id,
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
