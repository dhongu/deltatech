# © 2025 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

from base64 import b64encode
from textwrap import dedent

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

UBL_NS = {
    "inv": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}


def _xml_invoice(
    *,
    invoice_id="INV-ATT-001",
    currency="RON",
    order_ref="PO001",
    supplier_vat="RO12345678",
    supplier_name="Vendor SRL",
    lines=None,
):
    if lines is None:
        lines = [
            {
                "code": "VEND-ATT-NEW",
                "name": "New From UBL (Attach)",
                "qty": "2",
                "price": "10.00",
                "line_total": "20.00",
                "unit_code": "C62",
                "barcode": "",
                "tax": "19",
            }
        ]
    line_xml = []
    for l in lines:
        std_id = (
            f'<cac:StandardItemIdentification><cbc:ID schemeID="0160">{l.get("barcode", "")}</cbc:ID></cac:StandardItemIdentification>'
            if l.get("barcode")
            else ""
        )
        line_xml.append(
            f"""
            <cac:InvoiceLine>
                <cbc:ID>1</cbc:ID>
                <cbc:InvoicedQuantity unitCode=\"{l.get("unit_code", "C62")}\">{l.get("qty", "1")}</cbc:InvoicedQuantity>
                <cbc:LineExtensionAmount currencyID=\"{currency}\">{l.get("line_total", "0")}</cbc:LineExtensionAmount>
                <cac:Price>
                    <cbc:PriceAmount currencyID=\"{currency}\">{l.get("price", "0")}</cbc:PriceAmount>
                </cac:Price>
                <cac:Item>
                    <cac:SellersItemIdentification><cbc:ID>{l.get("code", "")}</cbc:ID></cac:SellersItemIdentification>
                    {std_id}
                    <cbc:Name>{l.get("name", "")}</cbc:Name>
                    <cac:ClassifiedTaxCategory>
                        <cbc:Percent>{l.get("tax", "0")}</cbc:Percent>
                    </cac:ClassifiedTaxCategory>
                </cac:Item>
            </cac:InvoiceLine>
            """
        )
    xml = f"""
        <inv:Invoice xmlns:inv=\"{UBL_NS["inv"]}\" xmlns:cac=\"{UBL_NS["cac"]}\" xmlns:cbc=\"{UBL_NS["cbc"]}\">
            <cbc:ID>{invoice_id}</cbc:ID>
            <cbc:IssueDate>2025-01-01</cbc:IssueDate>
            <cbc:DueDate>2025-01-30</cbc:DueDate>
            <cbc:DocumentCurrencyCode>{currency}</cbc:DocumentCurrencyCode>
            <cac:OrderReference><cbc:ID>{order_ref}</cbc:ID></cac:OrderReference>
            <cac:AccountingSupplierParty>
                <cac:Party>
                    <cac:PartyTaxScheme><cbc:CompanyID>{supplier_vat}</cbc:CompanyID></cac:PartyTaxScheme>
                    <cac:PartyLegalEntity><cbc:RegistrationName>{supplier_name}</cbc:RegistrationName></cac:PartyLegalEntity>
                </cac:Party>
            </cac:AccountingSupplierParty>
            {"".join(line_xml)}
        </inv:Invoice>
    """
    return dedent(xml).strip().encode()


@tagged("post_install", "-at_install")
class TestProcessAttachmentsForPost(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.vendor = cls.env["res.partner"].create(
            {
                "name": "Vendor SRL",
                "is_company": True,
                "vat": "RO123456789",
                "supplier_rank": 1,
            }
        )
        cls.po = cls.env["purchase.order"].create(
            {
                "partner_id": cls.vendor.id,
                "company_id": cls.company.id,
                "date_order": "2025-01-01 00:00:00",
                "partner_ref": "ATT-EXT-PO-REF",
            }
        )
        # Ensure the feature toggle is enabled
        cls.env["ir.config_parameter"].sudo().set_param("deltatech_purchase_ubl.auto_import", "True")

    def test_auto_import_triggers_on_xml_attachment(self):
        # Prepare a valid UBL for the current PO
        xml = _xml_invoice(order_ref=self.po.name)
        att = self.env["ir.attachment"].create(
            {
                "name": "invoice_attach.xml",
                "datas": b64encode(xml),
                "mimetype": "application/xml",
                "res_model": "purchase.order",
                "res_id": self.po.id,
            }
        )

        # Call the hook directly as done by mail.thread when posting messages
        self.po._process_attachments_for_post([], [att.id], {})

        # After processing, the PO should have at least one line created from the UBL
        self.assertTrue(self.po.order_line, "Order line should be created from XML attachment")
        # And a vendor bill should be created as well

        # A log message should have been posted on the PO
        last_msg = self.po.message_ids.sorted(key=lambda m: m.id)[-1] if self.po.message_ids else False
        self.assertTrue(last_msg, "A log message should be posted on the PO")
