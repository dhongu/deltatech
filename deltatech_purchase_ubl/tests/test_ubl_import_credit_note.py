# © 2026 Deltatech
# See README.rst file on addons root folder for license details


from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools.binary import BinaryBytes

from .test_ubl_import import UBL_NS, _xml_invoice

CREDIT_NOTE_NS = "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2"


def _credit_note(order_ref, supplier_vat, supplier_name, code, qty="1", price="10"):
    """A minimal UBL CreditNote document (CreditNoteLine / CreditedQuantity)."""
    return f"""<CreditNote xmlns="{CREDIT_NOTE_NS}" xmlns:cac="{UBL_NS["cac"]}" xmlns:cbc="{UBL_NS["cbc"]}">
        <cbc:ID>CN-001</cbc:ID>
        <cbc:IssueDate>2025-02-01</cbc:IssueDate>
        <cbc:CreditNoteTypeCode>381</cbc:CreditNoteTypeCode>
        <cbc:DocumentCurrencyCode>RON</cbc:DocumentCurrencyCode>
        <cac:OrderReference><cbc:ID>{order_ref}</cbc:ID></cac:OrderReference>
        <cac:AccountingSupplierParty><cac:Party>
            <cac:PartyTaxScheme><cbc:CompanyID>{supplier_vat}</cbc:CompanyID></cac:PartyTaxScheme>
            <cac:PartyLegalEntity><cbc:RegistrationName>{supplier_name}</cbc:RegistrationName></cac:PartyLegalEntity>
        </cac:Party></cac:AccountingSupplierParty>
        <cac:CreditNoteLine>
            <cbc:ID>1</cbc:ID>
            <cbc:CreditedQuantity unitCode="C62">{qty}</cbc:CreditedQuantity>
            <cbc:LineExtensionAmount currencyID="RON">{price}</cbc:LineExtensionAmount>
            <cac:Item>
                <cbc:Name>Credited item</cbc:Name>
                <cac:SellersItemIdentification><cbc:ID>{code}</cbc:ID></cac:SellersItemIdentification>
            </cac:Item>
            <cac:Price><cbc:PriceAmount currencyID="RON">{price}</cbc:PriceAmount></cac:Price>
        </cac:CreditNoteLine>
    </CreditNote>""".encode()


@tagged("post_install", "-at_install")
class TestUblImportCreditNote(TransactionCase):
    """Credit notes (CreditNote documents or Invoice type 381) are flagged, never applied."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.Wizard = cls.env["purchase.ubl.import.wizard"]
        cls.vendor = cls.env["res.partner"].create(
            {"name": "Credit Vendor SRL", "vat": "RO50000005", "supplier_rank": 1}
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Credit Product",
                "default_code": "CRED-1",
                "is_storable": True,
                "purchase_ok": True,
                "purchase_method": "purchase",
            }
        )

    def _order(self):
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "company_id": self.company.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 5.0,
                            "price_unit": 10.0,
                            "name": self.product.name,
                            "uom_id": self.product.uom_id.id,
                            "date_planned": "2025-01-01 00:00:00",
                        },
                    )
                ],
            }
        )
        order.button_confirm()
        return order

    def _invoice_381(self, order):
        xml = _xml_invoice(
            invoice_id="CN-381",
            order_ref=order.name,
            supplier_vat=self.vendor.vat,
            supplier_name=self.vendor.name,
            lines=[{"code": "CRED-1", "name": self.product.name, "qty": "-2", "price": "8", "line_total": "-16"}],
        )
        return xml.replace(b"<cbc:DueDate>", b"<cbc:InvoiceTypeCode>381</cbc:InvoiceTypeCode>\n<cbc:DueDate>", 1)

    def _wizard(self, order, xml, **vals):
        return self.Wizard.with_context(active_model="purchase.order", active_id=order.id).create(
            dict({"data_file": BinaryBytes(xml), "validate_receipt": True, "create_bill": True}, **vals)
        )

    def _assert_order_untouched(self, order):
        line = order.order_line
        self.assertEqual(len(line), 1)
        self.assertEqual(line.product_qty, 5.0)
        self.assertEqual(line.price_unit, 10.0)
        self.assertFalse(order.invoice_ids)
        self.assertNotEqual(order.picking_ids.state, "done")

    def test_document_type_detection(self):
        order = self._order()
        self.assertEqual(self.Wizard._parse_xml(self._invoice_381(order))["document_type"], "credit_note")
        cn = _credit_note(order.name, self.vendor.vat, self.vendor.name, "CRED-1")
        self.assertTrue(self.Wizard._is_ubl_invoice(cn))
        self.assertEqual(self.Wizard._parse_xml(cn)["document_type"], "credit_note")
        self.assertEqual(self.Wizard._parse_xml(_xml_invoice())["document_type"], "invoice")

    def test_invoice_381_with_negative_quantities_is_not_applied(self):
        order = self._order()
        seller_count = len(self.product.seller_ids)
        wizard = self._wizard(order, self._invoice_381(order))
        wizard.action_import()
        self._assert_order_untouched(order)
        self.assertEqual(len(self.product.seller_ids), seller_count, "Vendor prices are not updated")
        self.assertIn("is a credit note", wizard.log)
        self.assertIn("text-warning", wizard.log_html)
        self.assertTrue(wizard.has_warning)

    def test_credit_note_document_is_not_billed(self):
        order = self._order()
        xml = _credit_note(order.name, self.vendor.vat, self.vendor.name, "CRED-1")
        wizard = self._wizard(order, xml)
        wizard.action_import()
        self._assert_order_untouched(order)
        self.assertIn("CN-001 is a credit note", wizard.log)

    def test_preview_shows_the_warning_instead_of_lines(self):
        order = self._order()
        wizard = self._wizard(order, self._invoice_381(order))
        wizard.action_preview()
        self.assertEqual(wizard.state, "done")
        self.assertFalse(wizard.line_ids)
        self.assertIn("is a credit note", wizard.log)
        self._assert_order_untouched(order)

    def test_auto_import_schedules_review_activity(self):
        order = self._order()
        attachment = self.env["ir.attachment"].create(
            {
                "name": "credit_note.xml",
                "raw": _credit_note(order.name, self.vendor.vat, self.vendor.name, "CRED-1"),
                "mimetype": "application/xml",
                "res_model": "purchase.order",
                "res_id": order.id,
            }
        )
        self.env["ir.config_parameter"].sudo().set_bool("deltatech_purchase_ubl.auto_import", True)
        order._process_attachments_for_post([], [attachment.id], {})
        self._assert_order_untouched(order)
        self.assertTrue(order.activity_ids.filtered(lambda a: a.summary == "SPV import needs review"))
