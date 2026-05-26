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
    invoice_id="INV-001",
    currency="RON",
    order_ref="PO001",
    supplier_vat="RO123456789",
    supplier_name="Vendor SRL",
    lines=None,
):
    if lines is None:
        lines = [
            {
                "code": "VEND-001",
                "name": "Test Product",
                "qty": "2",
                "price": "10.5",
                "line_total": "21",
                "unit_code": "KGM",
                "barcode": "",
                "tax": "19",
            }
        ]
    line_xml = []
    for l in lines:
        std_id = (
            f"<cac:StandardItemIdentification><cbc:ID schemeID=\"0160\">{l.get('barcode','')}</cbc:ID></cac:StandardItemIdentification>"
            if l.get("barcode")
            else ""
        )
        allowance_xml = ""
        if l.get("allowance_amount"):
            allowance_xml = f"""
                <cac:AllowanceCharge>
                    <cbc:ChargeIndicator>false</cbc:ChargeIndicator>
                    <cbc:AllowanceChargeReason>{l.get('allowance_reason', 'Discount')}</cbc:AllowanceChargeReason>
                    <cbc:Amount currencyID=\"{currency}\">{l.get('allowance_amount')}</cbc:Amount>
                </cac:AllowanceCharge>"""
        line_xml.append(
            f"""
            <cac:InvoiceLine>
                <cbc:ID>1</cbc:ID>
                <cbc:InvoicedQuantity unitCode=\"{l.get('unit_code','C62')}\">{l.get('qty','1')}</cbc:InvoicedQuantity>
                <cbc:LineExtensionAmount currencyID=\"{currency}\">{l.get('line_total','0')}</cbc:LineExtensionAmount>
                {allowance_xml}
                <cac:Price>
                    <cbc:PriceAmount currencyID=\"{currency}\">{l.get('price','0')}</cbc:PriceAmount>
                </cac:Price>
                <cac:Item>
                    <cac:SellersItemIdentification><cbc:ID>{l.get('code','')}</cbc:ID></cac:SellersItemIdentification>
                    {std_id}
                    <cbc:Name>{l.get('name','')}</cbc:Name>
                    <cac:ClassifiedTaxCategory>
                        <cbc:Percent>{l.get('tax','0')}</cbc:Percent>
                    </cac:ClassifiedTaxCategory>
                </cac:Item>
            </cac:InvoiceLine>
            """
        )
    xml = f"""
        <inv:Invoice xmlns:inv=\"{UBL_NS['inv']}\" xmlns:cac=\"{UBL_NS['cac']}\" xmlns:cbc=\"{UBL_NS['cbc']}\">
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
            {''.join(line_xml)}
        </inv:Invoice>
    """
    return dedent(xml).strip().encode()


@tagged("post_install", "-at_install")
class TestPurchaseUblImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Company and Vendor
        cls.company = cls.env.ref("base.main_company")
        cls.vendor = cls.env["res.partner"].create(
            {
                "name": "Vendor SRL",
                "is_company": True,
                "vat": "RO123456789",
                "supplier_rank": 1,
            }
        )
        # Basic PO (empty) for the vendor
        cls.po_model = cls.env["purchase.order"]
        cls.po = cls.po_model.create(
            {
                "partner_id": cls.vendor.id,
                "company_id": cls.company.id,
                "date_order": "2025-01-01 00:00:00",
                "partner_ref": "EXT-PO-REF",
            }
        )

    def _run_wizard(self, xml_bytes, order):
        Wiz = self.env["purchase.ubl.import.wizard"]
        wiz = Wiz.with_context(active_model="purchase.order", active_id=order.id).create(
            {
                "data_file": b64encode(xml_bytes),
                "filename": "test.xml",
                "update_prices": True,
                "create_bill": False,
                "validate_receipt": True,
                "create_missing_products": True,
            }
        )
        wiz.action_import()
        return wiz

    def test_missing_product_is_created_and_order_line_added(self):
        xml = _xml_invoice(
            order_ref=self.po.name,
            lines=[
                {
                    "code": "VEND-NEW",
                    "name": "New From UBL",
                    "qty": "3",
                    "price": "12.50",
                    "line_total": "37.50",
                    "unit_code": "KGM",
                }
            ],
        )
        wiz = self._run_wizard(xml, self.po)

        # Product created with default_code and correct UoM
        product = self.env["product.product"].search([("name", "=", "New From UBL")], limit=1)
        self.assertTrue(product, "Product should be created from UBL line")
        self.assertEqual(product.uom_id, self.env.ref("uom.product_uom_kgm"))

        # Supplierinfo created with price in currency
        sinfo = self.env["product.supplierinfo"].search(
            [("partner_id", "=", self.vendor.id), ("product_tmpl_id", "=", product.product_tmpl_id.id)], limit=1
        )
        self.assertTrue(sinfo, "Supplierinfo should be created for vendor")
        self.assertEqual(sinfo.product_code, "VEND-NEW")
        self.assertAlmostEqual(sinfo.price, 12.50, places=2)

        # Order line should be added when PO had no lines
        self.assertTrue(self.po.order_line, "Order line should be added from XML when PO had no lines")
        pol = self.po.order_line.filtered(lambda l: l.product_id == product)
        self.assertTrue(pol)
        self.assertAlmostEqual(pol.product_qty, 3.0, places=4)
        self.assertAlmostEqual(pol.price_unit, 12.50, places=2)

        # Vendor bill should be created and linked
        # self.assertTrue(self.po.invoice_ids, "Vendor bill should be created")
        # inv = self.po.invoice_ids.sorted(key=lambda m: m.id)[-1]
        # self.assertEqual(inv.ref, "INV-001")
        # self.assertEqual(inv.invoice_origin, self.po.name)

        # Log includes created products
        self.assertIn("Created products", (wiz.log or ""))

    def test_existing_order_line_is_updated_by_code(self):
        # Create a product ahead with default_code that matches XML code
        kg_uom = self.env.ref("uom.product_uom_kgm")
        product = self.env["product.product"].create(
            {
                "name": "Existing",
                "default_code": "VEND-EXIST",
                "is_storable": True,
                "uom_id": kg_uom.id,
                "uom_po_id": kg_uom.id,
                "purchase_ok": True,
            }
        )
        # Create a PO line with that product
        self.env["purchase.order.line"].create(
            {
                "order_id": self.po.id,
                "product_id": product.id,
                "name": product.display_name,
                "product_qty": 1.0,
                "price_unit": 5.0,
                "product_uom": product.uom_po_id.id,
                "date_planned": "2025-01-01 00:00:00",
            }
        )
        xml = _xml_invoice(
            order_ref=self.po.name,
            lines=[
                {
                    "code": "VEND-EXIST",
                    "name": "Existing",
                    "qty": "7",
                    "price": "9.99",
                    "line_total": "69.93",
                    "unit_code": "KGM",
                }
            ],
        )
        _ = self._run_wizard(xml, self.po)

        pol = self.po.order_line.filtered(lambda l: l.product_id == product)
        self.assertTrue(pol)
        self.assertAlmostEqual(pol.product_qty, 7.0, places=4)
        self.assertAlmostEqual(pol.price_unit, 9.99, places=2)

        # Price in vendor pricelist also updated
        sinfo = self.env["product.supplierinfo"].search(
            [("partner_id", "=", self.vendor.id), ("product_tmpl_id", "=", product.product_tmpl_id.id)], limit=1
        )
        self.assertTrue(sinfo)
        self.assertAlmostEqual(sinfo.price, 9.99, places=2)

    def test_product_match_by_name_no_spaces(self):
        # Create a product with spaces in name
        product = self.env["product.product"].create(
            {
                "name": "Product With Spaces",
                "is_storable": True,
                "purchase_ok": True,
            }
        )
        # XML has name with different spaces
        xml = _xml_invoice(
            order_ref=self.po.name,
            lines=[
                {
                    "code": "XYZ",
                    "name": "Product  With  Spaces",
                    "qty": "1",
                    "price": "10.0",
                    "line_total": "10.0",
                }
            ],
        )
        self._run_wizard(xml, self.po)
        pol = self.po.order_line.filtered(lambda l: l.product_id == product)
        self.assertTrue(pol, "Should match product even if name in XML has different spaces")

    def test_match_product_on_order(self):
        # Create two products
        self.env["product.product"].create(
            {
                "name": "Product 1",
                "default_code": "P1",
                "is_storable": True,
            }
        )
        product_2 = self.env["product.product"].create(
            {
                "name": "Product 2",
                "default_code": "P2",
                "is_storable": True,
            }
        )
        # Add only product 2 to PO
        self.env["purchase.order.line"].create(
            {
                "order_id": self.po.id,
                "product_id": product_2.id,
                "name": product_2.display_name,
                "product_qty": 1.0,
                "price_unit": 5.0,
                "product_uom": product_2.uom_po_id.id,
                "date_planned": "2025-01-01 00:00:00",
            }
        )
        # XML has a code that matches both P1 (default_code) and P2 (supplier code)
        # But we want to see if it prefers the one on order if matched there
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.vendor.id,
                "product_tmpl_id": product_2.product_tmpl_id.id,
                "product_code": "VEND-P2",
            }
        )

        xml = _xml_invoice(
            order_ref=self.po.name,
            lines=[
                {
                    "code": "VEND-P2",
                    "name": "Product2",
                    "qty": "5",
                    "price": "15.0",
                    "line_total": "75.0",
                }
            ],
        )
        self._run_wizard(xml, self.po)
        self.assertEqual(len(self.po.order_line), 1)
        self.assertEqual(self.po.order_line.product_id, product_2)
        self.assertEqual(self.po.order_line.product_qty, 5.0)

    def test_allowance_charge_discount_applied_on_order_line(self):
        """Linia 2 din XML-ul real e-Factura SPV:
        PriceAmount=372.20, AllowanceCharge/Amount=93.05, qty=1
        => discount = 93.05 / (372.20 * 1) * 100 = 25.00%
        LineExtensionAmount=279.15 (pretul net dupa discount)
        """
        # Produs nou fara linii pe comanda => se creeaza linie noua
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "company_id": self.company.id,
                "date_order": "2025-01-01 00:00:00",
            }
        )
        xml = _xml_invoice(
            order_ref=po.name,
            lines=[
                {
                    "code": "12538693",
                    "name": "Poliester de curea",
                    "qty": "1.000",
                    "price": "372.20",
                    "line_total": "279.15",
                    "unit_code": "H87",
                    "tax": "21",
                    "allowance_amount": "93.05",
                    "allowance_reason": "-30RO",
                }
            ],
        )
        Wiz = self.env["purchase.ubl.import.wizard"]
        wiz = Wiz.with_context(active_model="purchase.order", active_id=po.id).create(
            {
                "data_file": b64encode(xml),
                "filename": "test_discount.xml",
                "update_prices": False,
                "create_bill": False,
                "validate_receipt": False,
                "create_missing_products": True,
            }
        )
        wiz.action_import()

        self.assertTrue(po.order_line, "Trebuie creata cel putin o linie pe comanda")
        pol = po.order_line[0]
        self.assertAlmostEqual(pol.price_unit, 372.20, places=2, msg="Pretul unitar trebuie sa fie pretul brut din XML")
        self.assertAlmostEqual(pol.product_qty, 1.0, places=3)

        if "discount" in self.env["purchase.order.line"]._fields:
            self.assertAlmostEqual(
                pol.discount,
                25.0,
                places=1,
                msg="Discount-ul trebuie sa fie ~25% (93.05 / 372.20 * 100)",
            )
