# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
 xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
 xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:ID>FV-1</cbc:ID>
  <cbc:DocumentCurrencyCode>RON</cbc:DocumentCurrencyCode>
  <cac:AccountingSupplierParty><cac:Party>
    <cac:PartyTaxScheme><cbc:CompanyID>RO12345674</cbc:CompanyID></cac:PartyTaxScheme>
    <cac:PartyLegalEntity><cbc:RegistrationName>Base Vendor</cbc:RegistrationName></cac:PartyLegalEntity>
  </cac:Party></cac:AccountingSupplierParty>
  <cac:LegalMonetaryTotal><cbc:PayableAmount>121.00</cbc:PayableAmount></cac:LegalMonetaryTotal>
  <cac:InvoiceLine>
    <cbc:InvoicedQuantity unitCode="KGM">10</cbc:InvoicedQuantity>
    <cbc:LineExtensionAmount>100.00</cbc:LineExtensionAmount>
    <cac:Item>
      <cbc:Name>Base Product</cbc:Name>
      <cac:SellersItemIdentification><cbc:ID>B-1</cbc:ID></cac:SellersItemIdentification>
      <cac:ClassifiedTaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>21</cbc:Percent></cac:ClassifiedTaxCategory>
    </cac:Item>
    <cac:Price><cbc:PriceAmount>10.00</cbc:PriceAmount></cac:Price>
  </cac:InvoiceLine>
</Invoice>"""


@tagged("post_install", "-at_install")
class TestAccountUblImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mixin = cls.env["account.ubl.import.mixin"]
        cls.vendor = cls.env["res.partner"].create({"name": "Base Vendor", "vat": "RO12345674", "supplier_rank": 1})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Base Product",
                "type": "consu",
                "seller_ids": [Command.create({"partner_id": cls.vendor.id, "product_code": "B-1", "price": 9.0})],
            }
        )

    def test_parse(self):
        data = self.mixin._parse_xml(XML)
        self.assertEqual(data["invoice_id"], "FV-1")
        self.assertEqual(data["payable_amount"], 121.0)
        self.assertEqual(len(data["lines"]), 1)
        line = data["lines"][0]
        self.assertEqual((line["code"], line["qty"], line["price"], line["tax_percent"]), ("B-1", 10.0, 10.0, 21.0))
        self.assertTrue(self.mixin._is_ubl_invoice(XML))
        self.assertFalse(self.mixin._is_ubl_invoice(b"not xml"))
        with self.assertRaises(UserError):
            self.mixin._parse_xml(b"<broken")

    def test_vendor_and_product(self):
        self.assertEqual(self.mixin._find_supplier_partner("12345674", ""), self.vendor)
        product, how = self.mixin._match_product_detailed(self.vendor, "B-1", "x")
        self.assertEqual((product, how), (self.product, "code"))
        self.assertEqual(self.mixin._uom_from_code("KGM"), self.env.ref("uom.product_uom_kgm"))

    def test_new_product_is_goods(self):
        product = self.mixin._create_product_from_xml_line(
            self.vendor, {"name": "New Thing", "code": "N-1", "price": 5.0, "unit_code": "C62"}, "RON"
        )
        self.assertEqual(product.type, "consu")
        self.assertEqual(product.seller_ids.product_code, "N-1")
