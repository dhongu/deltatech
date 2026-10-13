# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestInvoicePickingUom(TransactionCase):
    """PICKINV-001: picking quantities must be converted to the order line unit."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")
        cls.partner = cls.env["res.partner"].create({"name": "UoM Partner"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "UoM Product",
                "is_storable": True,
                "uom_id": cls.uom_unit.id,
                "invoice_policy": "order",
                "list_price": 10.0,
            }
        )
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)

    def test_supplier_invoice_converts_receipt_quantity(self):
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 1.0,
                            "product_uom_id": self.uom_dozen.id,
                            "price_unit": 120.0,
                            "tax_ids": [(5, 0, 0)],
                            "date_planned": fields.Datetime.now(),
                        },
                    )
                ],
            }
        )
        order.button_confirm()
        picking = order.picking_ids
        # the receipt move is in the product unit: 12 units for 1 dozen
        self.assertEqual(picking.move_ids.product_uom, self.uom_unit)
        self.assertEqual(picking.move_ids.product_uom_qty, 12.0)
        picking.move_ids.quantity = 12.0
        picking.move_ids.picked = True
        picking.button_validate()
        picking.supplier_invoice_number = "UOM/001"
        picking.action_create_supplier_invoice()

        bill = picking.account_move_id
        self.assertTrue(bill)
        line = bill.invoice_line_ids.filtered(lambda aml: aml.product_id == self.product)
        self.assertRecordValues(line, [{"product_uom_id": self.uom_dozen.id, "quantity": 1.0, "price_unit": 120.0}])
        self.assertAlmostEqual(bill.amount_untaxed, 120.0)

    def test_customer_invoice_converts_delivered_quantity(self):
        self.env["stock.quant"]._update_available_quantity(self.product, self.warehouse.lot_stock_id, 24.0)
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 2.0,
                            "product_uom_id": self.uom_dozen.id,
                            "price_unit": 120.0,
                            "tax_ids": [(5, 0, 0)],
                        },
                    )
                ],
            }
        )
        order.action_confirm()
        picking = order.picking_ids
        self.assertEqual(picking.move_ids.product_uom, self.uom_unit)
        # partial delivery: 12 units = 1 dozen out of 2
        picking.move_ids.quantity = 12.0
        picking.move_ids.picked = True
        picking.with_context(skip_backorder=True).button_validate()
        self.assertEqual(picking.state, "done")

        invoice = order.with_context(picking_ids=picking.ids)._create_invoices()
        line = invoice.invoice_line_ids.filtered(lambda aml: aml.product_id == self.product)
        self.assertRecordValues(line, [{"product_uom_id": self.uom_dozen.id, "quantity": 1.0, "price_unit": 120.0}])
        self.assertAlmostEqual(invoice.amount_untaxed, 120.0)
