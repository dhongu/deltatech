# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestInvoice(TransactionCase):
    product_b = None
    stock_location = None
    product_a = None
    partner_a = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner_a = cls.env["res.partner"].create({"name": "Test"})
        seller_ids = [(0, 0, {"name": cls.partner_a.id})]
        cls.product_a = cls.env["product.product"].create(
            {"name": "Test A", "type": "product", "standard_price": 100, "list_price": 150, "seller_ids": seller_ids}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Test B", "type": "product", "standard_price": 100, "list_price": 150, "seller_ids": seller_ids}
        )

        cls.po_vals = {
            "partner_id": cls.partner_a.id,
            "order_line": [
                (
                    0,
                    0,
                    {
                        "name": cls.partner_a.name,
                        "product_id": cls.product_a.id,
                        "product_qty": 5.0,
                        "product_uom": cls.product_a.uom_po_id.id,
                        "price_unit": 500.0,
                    },
                )
            ],
        }
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.env["stock.quant"]._update_available_quantity(cls.product_a, cls.stock_location, 1000)
        cls.env["stock.quant"]._update_available_quantity(cls.product_b, cls.stock_location, 1000)

    def test_create_invoice_from_purchase(self):
        self.po = self.env["purchase.order"].create(self.po_vals)
        self.po.button_confirm()
        self.picking = self.po.picking_ids[0]
        for ml in self.picking.move_line_ids:
            ml.qty_done = ml.product_uom_qty
        self.picking.button_validate()
        self.picking.supplier_invoice_number = "123"

        self.picking.action_create_supplier_invoice()

    def test_create_invoice_from_batch_purchase(self):
        self.po = self.env["purchase.order"].create(self.po_vals)
        self.po.button_confirm()
        self.picking_1 = self.po.picking_ids[0]
        self.picking_1.supplier_invoice_number = "321"
        for ml in self.picking_1.move_line_ids:
            ml.qty_done = ml.product_uom_qty

        self.po = self.env["purchase.order"].create(self.po_vals)
        self.po.button_confirm()
        self.picking_2 = self.po.picking_ids[0]
        self.picking_2.supplier_invoice_number = "321"
        for ml in self.picking_2.move_line_ids:
            ml.qty_done = ml.product_uom_qty

        batch_form = Form(self.env["stock.picking.batch"])
        batch_form.picking_ids.add(self.picking_1)
        batch_form.picking_ids.add(self.picking_2)

        batch_receipt = batch_form.save()
        batch_receipt.action_confirm()
        batch_receipt.action_done()

        batch_receipt.action_create_invoice()

    def test_create_invoice_from_sale(self):
        so = Form(self.env["sale.order"])
        so.partner_id = self.partner_a
        so.force_invoice_order = True
        with so.order_line.new() as so_line:
            so_line.product_id = self.product_a
            so_line.product_uom_qty = 100

        with so.order_line.new() as so_line:
            so_line.product_id = self.product_b
            so_line.product_uom_qty = 10

        self.so = so.save()
        self.so.action_confirm()

        self.picking = self.so.picking_ids[0]
        self.picking.action_assign()

        for ml in self.picking.move_line_ids:
            ml.qty_done = ml.product_uom_qty
        self.picking.button_validate()

        self.picking.action_create_invoice()

    def test_create_invoice_from_batch_sale(self):
        so = Form(self.env["sale.order"])
        so.partner_id = self.partner_a
        so.force_invoice_order = True
        with so.order_line.new() as so_line:
            so_line.product_id = self.product_a
            so_line.product_uom_qty = 100

        self.so = so.save()
        self.so.action_confirm()

        self.picking_1 = self.so.picking_ids[0]
        for ml in self.picking_1.move_line_ids:
            ml.qty_done = ml.product_uom_qty

        so = Form(self.env["sale.order"])
        so.partner_id = self.partner_a
        so.force_invoice_order = True
        with so.order_line.new() as so_line:
            so_line.product_id = self.product_a
            so_line.product_uom_qty = 100

        self.so = so.save()
        self.so.action_confirm()

        self.picking_2 = self.so.picking_ids[0]
        for ml in self.picking_2.move_line_ids:
            ml.qty_done = ml.product_uom_qty

        batch_form = Form(self.env["stock.picking.batch"])
        batch_form.picking_ids.add(self.picking_1)
        batch_form.picking_ids.add(self.picking_2)

        batch_sale = batch_form.save()
        batch_sale.action_confirm()
        batch_sale.action_done()

        batch_sale.action_create_invoice()
