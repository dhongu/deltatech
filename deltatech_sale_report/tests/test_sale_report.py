from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleReportPartnerEmail(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_a = cls.env["res.partner"].create({"name": "Client A", "email": "client.a@example.com"})
        cls.partner_b = cls.env["res.partner"].create({"name": "Client B", "email": "client.b@example.com"})
        cls.product = cls.env["product.product"].create({"name": "Produs test", "list_price": 100.0})

    def _create_order(self, partner, qty):
        order = self.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "order_line": [Command.create({"product_id": self.product.id, "product_uom_qty": qty})],
            }
        )
        order.action_confirm()
        return order

    def test_partner_email_in_report(self):
        order_a = self._create_order(self.partner_a, 2)
        order_b = self._create_order(self.partner_b, 3)
        self.env.flush_all()

        report = self.env["sale.report"].search(
            [("order_reference", "in", [f"sale.order,{order_a.id}", f"sale.order,{order_b.id}"])]
        )
        self.assertEqual(len(report), 2)
        emails = {line.order_reference.id: line.partner_email for line in report}
        self.assertEqual(emails[order_a.id], "client.a@example.com")
        self.assertEqual(emails[order_b.id], "client.b@example.com")

    def test_group_by_partner_email(self):
        self._create_order(self.partner_a, 2)
        self._create_order(self.partner_a, 4)
        self._create_order(self.partner_b, 3)
        self.env.flush_all()

        groups = self.env["sale.report"].formatted_read_group(
            [("partner_email", "in", ["client.a@example.com", "client.b@example.com"])],
            groupby=["partner_email"],
            aggregates=["product_uom_qty:sum"],
        )
        qty = {group["partner_email"]: group["product_uom_qty:sum"] for group in groups}
        self.assertEqual(qty["client.a@example.com"], 6.0)
        self.assertEqual(qty["client.b@example.com"], 3.0)
