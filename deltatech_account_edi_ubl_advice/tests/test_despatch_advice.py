# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from lxml import etree

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account_edi_ubl_cii.tests.common import TestUblCiiCommon


@tagged("post_install", "-at_install")
class TestDespatchAdvice(TestUblCiiCommon):
    """Referința la aviz (cac:DespatchDocumentReference) în exportul UBL BIS3.

    Modulul depinde doar de `account_edi_ubl_cii`; `sale`, `stock` și
    `sale_stock` sunt integrări opționale. Exportul trebuie să meargă pe orice
    combinație a lor (UBLADVICE-001).
    """

    def _despatch_ids(self, invoice):
        xml_content, _errors = self.env["account.edi.xml.ubl_bis3"]._export_invoice(invoice)
        root = etree.fromstring(xml_content)
        return root.xpath(
            "//cac:DespatchDocumentReference/cbc:ID/text()",
            namespaces={
                "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
                "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            },
        )

    def test_export_invoice_without_sale_order(self):
        """O factură de client fără comandă se exportă fără referință la aviz,
        indiferent dacă `sale`/`stock`/`sale_stock` sunt instalate."""
        invoice = self.env["account.move"].create(
            {
                "partner_id": self.partner_be.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [Command.create({"product_id": self.product_a.id, "price_unit": 100.0})],
            }
        )
        invoice.action_post()
        self.assertEqual(self._despatch_ids(invoice), [])

    def test_export_invoice_with_delivered_sale_order(self):
        """Cu `sale_stock`, factura unei comenzi livrate poartă numele avizului."""
        if "sale.order" not in self.env or "move_ids" not in self.env["sale.order.line"]._fields:
            self.skipTest("sale_stock nu este instalat")
        # utilizatorul de test din AccountTestInvoicingCommon are doar drepturi contabile
        self.env.user.group_ids |= self.env.ref("sales_team.group_sale_manager") | self.env.ref(
            "stock.group_stock_manager"
        )
        product = self.env["product.product"].create(
            {"name": "TEST UBL advice", "type": "consu", "invoice_policy": "order", "list_price": 100.0}
        )
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_be.id,
                "order_line": [Command.create({"product_id": product.id, "product_uom_qty": 2.0})],
            }
        )
        order.action_confirm()
        picking = order.picking_ids
        self.assertEqual(len(picking), 1)
        picking.move_ids.quantity = 2.0
        picking.move_ids.picked = True
        picking.button_validate()
        self.assertEqual(picking.state, "done")

        invoice = order._create_invoices()
        invoice.action_post()
        self.assertEqual(self._despatch_ids(invoice), [picking.name])
