# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestInvoicePickingAutomatically(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Partner
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})

        # Product
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "list_price": 100.0,
                "invoice_policy": "delivery",
            }
        )

        # Warehouse and picking type with create_invoice_automatically
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.picking_type_out = cls.warehouse.out_type_id
        cls.picking_type_out.write(
            {
                "create_invoice_automatically": True,
                "post_invoice_automatically": True,
            }
        )

    def _create_sale_order(self):
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 2,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        return sale_order

    def _confirm_and_validate_picking(self, sale_order):
        sale_order.action_confirm()
        picking = sale_order.picking_ids[0]
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        picking.button_validate()
        return picking

    def test_invoice_state_set_on_done(self):
        """La validarea picking-ului, invoice_state trebuie setat pe 'to_invoice'."""
        sale_order = self._create_sale_order()
        picking = self._confirm_and_validate_picking(sale_order)
        self.assertEqual(
            picking.invoice_state,
            "to_invoice",
            "invoice_state trebuie sa fie 'to_invoice' dupa validarea picking-ului",
        )

    def test_cron_generates_and_posts_invoice(self):
        """Cronul trebuie sa genereze si sa posteze factura, si sa marcheze picking-ul ca 'invoiced'."""
        sale_order = self._create_sale_order()
        picking = self._confirm_and_validate_picking(sale_order)
        self.assertEqual(picking.invoice_state, "to_invoice")

        # Rulam cronul
        self.env["stock.picking"]._cron_generate_invoices()

        self.assertEqual(
            picking.invoice_state,
            "invoiced",
            "invoice_state trebuie sa fie 'invoiced' dupa rularea cronului",
        )

        invoices = sale_order.invoice_ids
        self.assertTrue(invoices, "Trebuie sa existe cel putin o factura generata")
        self.assertTrue(
            all(inv.state == "posted" for inv in invoices),
            "Toate facturile trebuie sa fie postate (post_invoice_automatically=True)",
        )

    def test_cron_no_invoice_when_flag_disabled(self):
        """Daca create_invoice_automatically=False, picking-ul nu trebuie sa aiba invoice_state setat."""
        self.picking_type_out.write({"create_invoice_automatically": False})
        try:
            sale_order = self._create_sale_order()
            picking = self._confirm_and_validate_picking(sale_order)
            self.assertFalse(
                picking.invoice_state,
                "invoice_state nu trebuie setat daca create_invoice_automatically=False",
            )
        finally:
            self.picking_type_out.write({"create_invoice_automatically": True})

    def test_cron_invoice_not_posted_when_post_disabled(self):
        """Daca post_invoice_automatically=False, factura trebuie sa ramana in draft."""
        self.picking_type_out.write({"post_invoice_automatically": False})
        try:
            sale_order = self._create_sale_order()
            picking = self._confirm_and_validate_picking(sale_order)
            self.assertEqual(picking.invoice_state, "to_invoice")

            self.env["stock.picking"]._cron_generate_invoices()

            invoices = sale_order.invoice_ids
            self.assertTrue(invoices, "Trebuie sa existe cel putin o factura generata")
            self.assertTrue(
                all(inv.state == "draft" for inv in invoices),
                "Facturile trebuie sa ramana in draft daca post_invoice_automatically=False",
            )
        finally:
            self.picking_type_out.write({"post_invoice_automatically": True})
