from odoo.exceptions import UserError
from odoo.tests import common, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class TestSaleOrder(common.TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a sale order phase

        self.send_email_phase = self.env["sale.order.phase"].create(
            {
                "name": "Send Email phase",
                "send_email": True,
                "sequence": 1,
            }
        )

        self.phase_confirmed = self.env["sale.order.phase"].create(
            {
                "name": "Test phase",
                "sequence": 2,
                "send_email": True,
                "confirmed": True,
            }
        )

        self.phase_invoiced = self.env["sale.order.phase"].create(
            {
                "name": "Invoiced phase",
                "invoiced": True,
                "sequence": 3,
            }
        )

        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        # Create a sale order
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "phase_id": self.phase_confirmed.id,
            }
        )

        # Create a picking type
        self.picking_type = self.env["stock.picking.type"].create(
            {
                "name": "Test Picking Type",
                "sequence": 1,
                "phase_id": self.phase_confirmed.id,
                "sequence_code": "TEST",  # Add this line
                "code": "internal",  # Add this line
            }
        )

        # Create a stock picking
        self.stock_picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type.id,
            }
        )
        self.stock_picking.sale_id = self.sale_order

    def test_sale_order_phase_creation(self):
        # Test the creation of a sale order phase
        self.assertEqual(self.phase_confirmed.name, "Test phase")
        self.assertEqual(self.phase_confirmed.sequence, 2)
        self.assertEqual(self.phase_confirmed.confirmed, True)

    def test_sale_order_creation(self):
        # Test the creation of a sale order
        self.assertEqual(self.sale_order.phase_id, self.phase_confirmed)

    def test_stock_picking_creation(self):
        # Test the creation of a stock picking
        self.assertEqual(self.stock_picking.sale_id, self.sale_order)
        self.assertEqual(self.stock_picking.picking_type_id, self.picking_type)

    def test_action_done(self):
        # Test the _action_done method
        self.stock_picking._action_done()
        self.assertEqual(self.sale_order.phase_id, self.phase_confirmed)

    def test_set_phase(self):
        # Test the set_phase method
        self.sale_order.set_phase("confirmed")
        self.assertEqual(self.sale_order.phase_id.confirmed, True)

    def test_write(self):
        # Test the write method
        self.sale_order.write({"phase_id": self.phase_confirmed.id})
        self.assertEqual(self.sale_order.phase_id, self.phase_confirmed)

    def test_onchange_phase_id(self):
        # Test the onchange_phase_id method
        self.sale_order.phase_id = self.phase_invoiced
        self.sale_order.invoice_status = "invoiced"
        with self.assertRaises(UserError):
            self.sale_order.onchange_phase_id()

    def test_action_confirm(self):
        # Test the action_confirm method
        self.sale_order.action_confirm()

    def test_action_quotation_sent(self):
        # Test the action_quotation_sent method

        self.sale_order.action_quotation_sent()
        self.assertEqual(self.sale_order.phase_id.send_email, True)


@tagged("post_install", "-at_install")
class TestSaleOrderInvoicedPhase(AccountTestInvoicingCommon):
    @classmethod
    def get_default_groups(cls):
        # fazele de comandă se configurează de managerul de vânzări
        return super().get_default_groups() | cls.env.ref("sales_team.group_sale_manager")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.phase_confirmed = cls.env["sale.order.phase"].create(
            {"name": "Confirmed phase", "confirmed": True, "sequence": 2}
        )
        cls.phase_invoiced = cls.env["sale.order.phase"].create(
            {"name": "Invoiced phase", "invoiced": True, "sequence": 3}
        )
        cls.service = cls.env["product.product"].create(
            {"name": "Test service", "type": "service", "invoice_policy": "order", "list_price": 100}
        )

    def test_invoice_post_sets_invoiced_phase(self):
        # la validarea facturii, comanda complet facturată trece în faza „facturat”
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_a.id,
                "order_line": [(0, 0, {"product_id": self.service.id, "product_uom_qty": 1})],
            }
        )
        order.action_confirm()
        self.assertEqual(order.phase_id, self.phase_confirmed)
        invoice = order._create_invoices()
        self.assertEqual(order.phase_id, self.phase_confirmed)
        invoice.action_post()
        self.assertEqual(order.invoice_status, "invoiced")
        self.assertEqual(order.phase_id, self.phase_invoiced)
