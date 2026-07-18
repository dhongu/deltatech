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
    tax_amount=None,
    tax_exclusive_amount=None,
    tax_inclusive_amount=None,
    payable_amount=None,
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
            f'<cac:StandardItemIdentification><cbc:ID schemeID="0160">{l.get("barcode", "")}</cbc:ID></cac:StandardItemIdentification>'
            if l.get("barcode")
            else ""
        )
        allowance_xml = ""
        if l.get("allowance_amount"):
            allowance_xml = f"""
                <cac:AllowanceCharge>
                    <cbc:ChargeIndicator>false</cbc:ChargeIndicator>
                    <cbc:AllowanceChargeReason>{l.get("allowance_reason", "Discount")}</cbc:AllowanceChargeReason>
                    <cbc:Amount currencyID=\"{currency}\">{l.get("allowance_amount")}</cbc:Amount>
                </cac:AllowanceCharge>"""
        line_xml.append(
            f"""
            <cac:InvoiceLine>
                <cbc:ID>1</cbc:ID>
                <cbc:InvoicedQuantity unitCode=\"{l.get("unit_code", "C62")}\">{l.get("qty", "1")}</cbc:InvoicedQuantity>
                <cbc:LineExtensionAmount currencyID=\"{currency}\">{l.get("line_total", "0")}</cbc:LineExtensionAmount>
                {allowance_xml}
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
    tax_total_xml = ""
    monetary_total_xml = ""
    if tax_amount is not None:
        tax_total_xml = f"""
            <cac:TaxTotal>
                <cbc:TaxAmount currencyID="{currency}">{tax_amount}</cbc:TaxAmount>
            </cac:TaxTotal>
        """
    if any(value is not None for value in [tax_exclusive_amount, tax_inclusive_amount, payable_amount]):
        monetary_total_xml = f"""
            <cac:LegalMonetaryTotal>
                <cbc:LineExtensionAmount currencyID="{currency}">{tax_exclusive_amount or "0"}</cbc:LineExtensionAmount>
                <cbc:TaxExclusiveAmount currencyID="{currency}">{tax_exclusive_amount or "0"}</cbc:TaxExclusiveAmount>
                <cbc:TaxInclusiveAmount currencyID="{currency}">{tax_inclusive_amount or tax_exclusive_amount or "0"}</cbc:TaxInclusiveAmount>
                <cbc:PayableAmount currencyID="{currency}">{payable_amount or tax_inclusive_amount or tax_exclusive_amount or "0"}</cbc:PayableAmount>
            </cac:LegalMonetaryTotal>
        """
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
            {tax_total_xml}
            {monetary_total_xml}
            {"".join(line_xml)}
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
        self.assertEqual(wiz.order_id, order)
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
                "product_uom_id": product.uom_id.id,
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

    def test_new_product_added_as_line_when_order_already_has_lines(self):
        # PO already has one line for an existing product
        kg_uom = self.env.ref("uom.product_uom_kgm")
        existing_product = self.env["product.product"].create(
            {
                "name": "Existing",
                "default_code": "VEND-EXIST",
                "is_storable": True,
                "uom_id": kg_uom.id,
                "purchase_ok": True,
            }
        )
        self.env["purchase.order.line"].create(
            {
                "order_id": self.po.id,
                "product_id": existing_product.id,
                "name": existing_product.display_name,
                "product_qty": 1.0,
                "price_unit": 5.0,
                "product_uom_id": existing_product.uom_id.id,
                "date_planned": "2025-01-01 00:00:00",
            }
        )
        # Invoice matches the existing line AND has an extra product not yet on the order
        # (e.g. an "Ecovaloare" line added by the supplier that was not on the original PO)
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
                },
                {
                    "code": "VEND-NEW",
                    "name": "New From UBL",
                    "qty": "3",
                    "price": "12.50",
                    "line_total": "37.50",
                    "unit_code": "KGM",
                },
            ],
        )
        _ = self._run_wizard(xml, self.po)

        # Existing line still updated
        pol_existing = self.po.order_line.filtered(lambda l: l.product_id == existing_product)
        self.assertTrue(pol_existing)
        self.assertAlmostEqual(pol_existing.product_qty, 7.0, places=4)

        # New product must be added as a new order line, not silently dropped
        new_product = self.env["product.product"].search([("name", "=", "New From UBL")], limit=1)
        self.assertTrue(new_product, "Product should be created from UBL line")
        pol_new = self.po.order_line.filtered(lambda l: l.product_id == new_product)
        self.assertTrue(pol_new, "New product from invoice must be added as a purchase order line")
        self.assertAlmostEqual(pol_new.product_qty, 3.0, places=4)
        self.assertAlmostEqual(pol_new.price_unit, 12.50, places=2)

    def test_vendor_bill_auto_created_when_invoice_id_present(self):
        # Even with create_bill unticked, a vendor bill must be created (and its ref/date
        # filled from the source document) whenever the source has an invoice number,
        # otherwise the supplier's invoice reference/date are lost.
        kg_uom = self.env.ref("uom.product_uom_kgm")
        product = self.env["product.product"].create(
            {
                "name": "Existing",
                "default_code": "VEND-EXIST",
                "is_storable": True,
                "uom_id": kg_uom.id,
                "purchase_ok": True,
                "purchase_method": "purchase",
            }
        )
        self.env["purchase.order.line"].create(
            {
                "order_id": self.po.id,
                "product_id": product.id,
                "name": product.display_name,
                "product_qty": 7.0,
                "price_unit": 9.99,
                "product_uom_id": product.uom_id.id,
                "date_planned": "2025-01-01 00:00:00",
            }
        )
        self.po.button_confirm()
        xml = _xml_invoice(
            invoice_id="INV-777",
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
        Wiz = self.env["purchase.ubl.import.wizard"]
        wiz = Wiz.with_context(active_model="purchase.order", active_id=self.po.id).create(
            {
                "data_file": b64encode(xml),
                "filename": "test.xml",
                "update_prices": True,
                "create_bill": False,
                "validate_receipt": False,
                "create_missing_products": True,
            }
        )
        wiz.action_import()

        self.assertTrue(self.po.invoice_ids, "Vendor bill should be auto-created when source has an invoice number")
        inv = self.po.invoice_ids.sorted(key=lambda m: m.id)[-1]
        self.assertEqual(inv.ref, "INV-777")
        self.assertEqual(str(inv.invoice_date), "2025-01-01")

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
                "product_uom_id": product_2.uom_id.id,
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

    def test_import_without_purchase_order_context_uses_xml_supplier(self):
        unit_uom = self.env.ref("uom.product_uom_unit")
        product = self.env["product.product"].create(
            {
                "name": "Standalone Import Product",
                "is_storable": True,
                "purchase_ok": True,
                "uom_id": unit_uom.id,
            }
        )
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.vendor.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "product_id": product.id,
                "product_code": "STANDALONE-CODE",
                "price": 5.0,
                "currency_id": self.env.ref("base.RON").id,
                "delay": 1,
            }
        )

        xml = _xml_invoice(
            order_ref="PO-NOT-IN-CONTEXT",
            supplier_vat=self.vendor.vat,
            supplier_name=self.vendor.name,
            lines=[
                {
                    "code": "STANDALONE-CODE",
                    "name": product.name,
                    "qty": "4",
                    "price": "11.25",
                    "line_total": "45.00",
                    "unit_code": "C62",
                }
            ],
        )
        wiz = self.env["purchase.ubl.import.wizard"].create(
            {
                "data_file": b64encode(xml),
                "filename": "standalone.xml",
                "update_prices": True,
                "create_bill": False,
                "validate_receipt": False,
                "create_missing_products": False,
            }
        )

        wiz.action_import()

        sinfo = self.env["product.supplierinfo"].search(
            [("partner_id", "=", self.vendor.id), ("product_tmpl_id", "=", product.product_tmpl_id.id)],
            limit=1,
        )
        self.assertAlmostEqual(sinfo.price, 11.25, places=2)
        self.assertIn("Vendor: Vendor SRL", wiz.log or "")
        self.assertIn("Order: - | XML Reference: PO-NOT-IN-CONTEXT", wiz.log or "")

    def test_import_uses_order_id_after_context_is_lost(self):
        xml = _xml_invoice(
            order_ref=self.po.name,
            lines=[
                {
                    "code": "CTX-LOST",
                    "name": "Context Lost Product",
                    "qty": "2",
                    "price": "9.50",
                    "line_total": "19.00",
                    "unit_code": "C62",
                }
            ],
        )
        wiz = (
            self.env["purchase.ubl.import.wizard"]
            .with_context(active_model="purchase.order", active_id=self.po.id)
            .create(
                {
                    "data_file": b64encode(xml),
                    "filename": "context_lost.xml",
                    "update_prices": True,
                    "create_bill": False,
                    "validate_receipt": False,
                    "create_missing_products": True,
                }
            )
        )

        wiz.action_import()

        self.assertEqual(wiz.order_id, self.po)
        self.assertTrue(self.po.order_line.filtered(lambda l: l.product_id.name == "Context Lost Product"))

    def test_total_check_warning_is_shown_when_xml_total_differs(self):
        # Use a fresh PO so accumulated lines from other tests don't affect the total
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "company_id": self.company.id,
                "date_order": "2025-01-01 00:00:00",
            }
        )
        product = self.env["product.product"].create(
            {
                "name": "Mismatch Product",
                "default_code": "MISMATCH",
                "is_storable": True,
                "purchase_ok": True,
            }
        )
        self.env["purchase.order.line"].create(
            {
                "order_id": po.id,
                "product_id": product.id,
                "name": product.display_name,
                "product_qty": 1.0,
                "price_unit": 10.0,
                "product_uom_id": product.uom_id.id,
                "date_planned": "2025-01-01 00:00:00",
                "tax_ids": [(5, 0, 0)],
            }
        )
        xml = _xml_invoice(
            order_ref=po.name,
            tax_exclusive_amount="15.00",
            tax_inclusive_amount="15.00",
            payable_amount="15.00",
            lines=[
                {
                    "code": "MISMATCH",
                    "name": product.name,
                    "qty": "1",
                    "price": "10.00",
                    "line_total": "10.00",
                    "unit_code": "C62",
                }
            ],
        )
        wiz = (
            self.env["purchase.ubl.import.wizard"]
            .with_context(active_model="purchase.order", active_id=po.id)
            .create(
                {
                    "data_file": b64encode(xml),
                    "filename": "mismatch.xml",
                    "update_prices": False,
                    "create_bill": False,
                    "validate_receipt": False,
                    "create_missing_products": False,
                }
            )
        )

        # Check message content without hardcoding the currency (company currency may vary)
        self.assertIn("differs from XML total 15.00", wiz.total_check_warning or "")

    def test_service_line_receive_policy_is_marked_received_for_billing(self):
        """Regression test for the reported Marso "Ecovaloare" bug: a service product
        with purchase_method="receive" has no stock moves, so its qty_received stays 0
        unless set explicitly -- otherwise action_create_invoice() silently drops the
        line from the vendor bill even though it is present on the purchase order.
        """
        eco = self.env["product.product"].create(
            {
                "name": "Ecovaloare ANVELOPA 15",
                "default_code": "ECO-15",
                "type": "service",
                "purchase_ok": True,
                "purchase_method": "receive",
            }
        )
        self.env["purchase.order.line"].create(
            {
                "order_id": self.po.id,
                "product_id": eco.id,
                "name": eco.display_name,
                "product_qty": 4.0,
                "price_unit": 1.50,
                "product_uom_id": eco.uom_id.id,
                "date_planned": "2025-01-01 00:00:00",
            }
        )
        self.po.button_confirm()
        self.assertEqual(
            self.po.order_line.qty_received,
            0.0,
            "Sanity check: a fresh service line has no received quantity yet",
        )

        xml = _xml_invoice(
            invoice_id="INV-ECO-1",
            order_ref=self.po.name,
            lines=[
                {
                    "code": "ECO-15",
                    "name": "Ecovaloare ANVELOPA 15",
                    "qty": "4",
                    "price": "1.50",
                    "line_total": "6.00",
                    "unit_code": "C62",
                }
            ],
        )
        Wiz = self.env["purchase.ubl.import.wizard"]
        wiz = Wiz.with_context(active_model="purchase.order", active_id=self.po.id).create(
            {
                "data_file": b64encode(xml),
                "filename": "eco.xml",
                "update_prices": True,
                "create_bill": True,
                "validate_receipt": False,
                "create_missing_products": True,
            }
        )
        wiz.action_import()

        pol = self.po.order_line.filtered(lambda l: l.product_id == eco)
        self.assertEqual(pol.qty_received_method, "manual")
        self.assertAlmostEqual(
            pol.qty_received,
            4.0,
            places=4,
            msg="Service line must be marked as received so it can be invoiced",
        )

        self.assertTrue(self.po.invoice_ids, "Vendor bill should be created")
        bill = self.po.invoice_ids.sorted(key=lambda m: m.id)[-1]
        bill_line = bill.invoice_line_ids.filtered(lambda l: l.product_id == eco)
        self.assertTrue(bill_line, "Ecovaloare line must reach the vendor bill, not be silently dropped")

    def test_total_check_log_confirms_when_totals_match(self):
        # Use a fresh PO with a line whose total exactly matches the XML payable_amount
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "company_id": self.company.id,
                "date_order": "2025-01-01 00:00:00",
            }
        )
        product = self.env["product.product"].create(
            {
                "name": "Total Check Product",
                "default_code": "TOTAL-OK",
                "is_storable": True,
                "purchase_ok": True,
            }
        )
        self.env["purchase.order.line"].create(
            {
                "order_id": po.id,
                "product_id": product.id,
                "name": product.display_name,
                "product_qty": 2.0,
                "price_unit": 9.50,
                "product_uom_id": product.uom_id.id,
                "date_planned": "2025-01-01 00:00:00",
                "tax_ids": [(5, 0, 0)],
            }
        )
        xml = _xml_invoice(
            order_ref=po.name,
            tax_exclusive_amount="19.00",
            tax_inclusive_amount="19.00",
            payable_amount="19.00",
            lines=[
                {
                    "code": "TOTAL-OK",
                    "name": "Total Check Product",
                    "qty": "2",
                    "price": "9.50",
                    "line_total": "19.00",
                    "unit_code": "C62",
                }
            ],
        )

        Wiz = self.env["purchase.ubl.import.wizard"]
        wiz = Wiz.with_context(active_model="purchase.order", active_id=po.id).create(
            {
                "data_file": b64encode(xml),
                "filename": "total_ok.xml",
                "update_prices": True,
                "create_bill": False,
                "validate_receipt": False,
                "create_missing_products": False,
            }
        )
        wiz.action_import()

        self.assertIn("Total check OK", wiz.log or "")

    def _confirmed_po_with_line(self, *, product=None, qty=3.0, price=10.0, tax=None):
        """Create and confirm a purchase order with a single line, so Odoo's
        native purchase flow auto-generates a receipt (stock.picking) for it —
        needed to exercise the real receipt-validation and bill-creation code
        paths (they are no-ops on an order with no lines/receipt)."""
        if product is None:
            product = self.env["product.product"].create(
                {
                    "name": "Bill/Receipt Flow Product",
                    "default_code": "BILLPROD",
                    "is_storable": True,
                    "purchase_ok": True,
                }
            )
        line_vals = {
            "product_id": product.id,
            "product_qty": qty,
            "price_unit": price,
            "name": product.name,
            "product_uom_id": product.uom_id.id,
            "date_planned": "2025-01-01 00:00:00",
        }
        if tax:
            line_vals["tax_ids"] = [(6, 0, tax.ids)]
        po = self.po_model.create(
            {
                "partner_id": self.vendor.id,
                "company_id": self.company.id,
                "order_line": [(0, 0, line_vals)],
            }
        )
        po.button_confirm()
        return po, product

    def test_create_vendor_bill_from_confirmed_order(self):
        """Exercises _create_vendor_bill / _apply_xml_taxes_to_bill / action_view_vendor_bill
        and the "Vendor bill created" log message — every other test uses create_bill=False,
        so this whole flow was previously untested."""
        tax_21 = self.env["account.tax"].create(
            {
                "name": "COVTEST Purchase 21%",
                "type_tax_use": "purchase",
                "amount_type": "percent",
                "amount": 21,
                "company_id": self.company.id,
            }
        )
        po, product = self._confirmed_po_with_line(tax=tax_21)

        xml = _xml_invoice(
            invoice_id="BILL-INV-1",
            order_ref=po.name,
            supplier_vat=self.vendor.vat,
            supplier_name=self.vendor.name,
            lines=[
                {
                    "code": "BILLPROD",
                    "name": product.name,
                    "qty": "3",
                    "price": "10.0",
                    "line_total": "30.0",
                    "tax": "21",
                }
            ],
        )
        wiz = (
            self.env["purchase.ubl.import.wizard"]
            .with_context(active_model="purchase.order", active_id=po.id)
            .create(
                {
                    "data_file": b64encode(xml),
                    "filename": "bill.xml",
                    "update_prices": False,
                    "create_bill": True,
                    "validate_receipt": False,
                    "create_missing_products": False,
                }
            )
        )
        wiz.action_import()

        self.assertTrue(po.invoice_ids, "Vendor bill should be created")
        bill = po.invoice_ids[0]
        self.assertEqual(bill.ref, "BILL-INV-1")
        self.assertEqual(wiz.bill_id, bill)
        self.assertIn("Vendor bill created", wiz.log or "")
        self.assertEqual(bill.invoice_line_ids.tax_ids, tax_21)

        # action_view_vendor_bill should resolve back to this order/bill without error
        action = wiz.action_view_vendor_bill()
        self.assertIsInstance(action, dict)

        # Re-running the same import should detect the duplicate ref and skip creating a second bill
        wiz2 = (
            self.env["purchase.ubl.import.wizard"]
            .with_context(active_model="purchase.order", active_id=po.id)
            .create(
                {
                    "data_file": b64encode(xml),
                    "filename": "bill.xml",
                    "update_prices": False,
                    "create_bill": True,
                    "validate_receipt": False,
                    "create_missing_products": False,
                }
            )
        )
        wiz2.action_import()
        self.assertEqual(wiz2.bill_id, bill)
        self.assertIn("already exists", wiz2.log or "")
        self.assertEqual(len(po.invoice_ids), 1, "No second bill should have been created")

    def test_validate_receipt_updates_real_picking(self):
        """Exercises _validate_receipt_quantities with an order (the real stock.picking
        branch) — every other test either has validate_receipt=False or no actual
        receipt to find, so this path (~40 lines) was previously untested."""
        po, product = self._confirmed_po_with_line(qty=3.0, price=10.0)
        picking = po.picking_ids
        self.assertTrue(picking, "Confirming the PO should generate a receipt")
        self.assertNotEqual(picking.state, "done")

        xml = _xml_invoice(
            order_ref=po.name,
            supplier_vat=self.vendor.vat,
            supplier_name=self.vendor.name,
            lines=[
                {
                    "code": "BILLPROD",
                    "name": product.name,
                    "qty": "3",
                    "price": "10.0",
                    "line_total": "30.0",
                }
            ],
        )
        wiz = (
            self.env["purchase.ubl.import.wizard"]
            .with_context(active_model="purchase.order", active_id=po.id)
            .create(
                {
                    "data_file": b64encode(xml),
                    "filename": "receipt.xml",
                    "update_prices": False,
                    "create_bill": False,
                    "validate_receipt": True,
                    "create_missing_products": False,
                }
            )
        )
        wiz.action_import()

        self.assertEqual(picking.state, "done", "Receipt should be validated (done)")
        self.assertIn("Receipt updated", wiz.log or "")

    def test_unmatched_product_without_order_is_reported_as_danger(self):
        """Exercises the 'Unmatched products' message and its _classify_message
        'danger' branch — no existing test leaves create_missing_products=False
        with a genuinely unmatched line."""
        xml = _xml_invoice(
            order_ref="NON-EXISTENT-PO",
            supplier_vat=self.vendor.vat,
            supplier_name=self.vendor.name,
            lines=[
                {
                    "code": "NO-SUCH-CODE",
                    "name": "No Such Product",
                    "qty": "1",
                    "price": "5.0",
                    "line_total": "5.0",
                }
            ],
        )
        wiz = self.env["purchase.ubl.import.wizard"].create(
            {
                "data_file": b64encode(xml),
                "filename": "unmatched.xml",
                "update_prices": False,
                "create_bill": False,
                "validate_receipt": False,
                "create_missing_products": False,
            }
        )
        wiz.action_import()

        self.assertIn("Unmatched products", wiz.log or "")
        self.assertIn("danger", wiz.log_html or "")

    def test_order_lines_warning_reflects_existing_lines(self):
        """_compute_order_lines_warning was never read by any existing test."""
        empty_po = self.po_model.create(
            {
                "partner_id": self.vendor.id,
                "company_id": self.company.id,
            }
        )
        wiz_empty = (
            self.env["purchase.ubl.import.wizard"]
            .with_context(active_model="purchase.order", active_id=empty_po.id)
            .new({})
        )
        self.assertFalse(wiz_empty.order_lines_warning)

        po_with_line, _product = self._confirmed_po_with_line()
        wiz_with_line = (
            self.env["purchase.ubl.import.wizard"]
            .with_context(active_model="purchase.order", active_id=po_with_line.id)
            .new({})
        )
        self.assertTrue(wiz_with_line.order_lines_warning)

    def test_resolve_currency_falls_back_to_company_currency(self):
        Wiz = self.env["purchase.ubl.import.wizard"]
        wiz = Wiz.new({})
        self.assertEqual(wiz._resolve_currency("NOT-A-REAL-CURRENCY"), self.company.currency_id)

    def test_uom_from_code_falls_back_to_unit(self):
        Wiz = self.env["purchase.ubl.import.wizard"]
        wiz = Wiz.new({})
        self.assertEqual(wiz._uom_from_code("NOT-A-REAL-UNIT-CODE"), self.env.ref("uom.product_uom_unit"))

    def test_find_supplier_partner_matches_vat_ignoring_spaces(self):
        partner = self.env["res.partner"].create(
            {
                "name": "Spaced VAT Vendor",
                "is_company": True,
                "vat": "RO999888777",
                "supplier_rank": 1,
            }
        )
        Wiz = self.env["purchase.ubl.import.wizard"]
        wiz = Wiz.new({})
        found = wiz._find_supplier_partner("RO 999888777", "")
        self.assertEqual(found, partner)

    def test_validate_receipt_quantities_fallback_without_order(self):
        """_validate_receipt_quantities(picking, line_map) without an order argument
        is only reachable if called directly (the wizard flow always passes order=...
        when it has one) — covers the button_validate()/backorder fallback branch."""
        po, product = self._confirmed_po_with_line(qty=2.0)
        picking = po.picking_ids
        Wiz = self.env["purchase.ubl.import.wizard"]
        wiz = Wiz.new({})
        result = wiz._validate_receipt_quantities(picking, {product.id: 2.0})
        self.assertTrue(result)
        self.assertEqual(picking.state, "done")

    def test_find_duplicate_bill_guards_missing_ref_or_partner(self):
        Wiz = self.env["purchase.ubl.import.wizard"]
        wiz = Wiz.new({})
        self.assertFalse(wiz._find_duplicate_bill(self.vendor, False))
        self.assertFalse(wiz._find_duplicate_bill(False, "SOME-REF"))

    def test_apply_xml_taxes_to_bill_noop_without_tax_percent(self):
        """When no mapped line carries a tax_percent, the method must return
        early without touching any invoice line."""
        po, product = self._confirmed_po_with_line()
        po.action_create_invoice()
        bill = po.invoice_ids[0]
        original_taxes = bill.invoice_line_ids.mapped("tax_ids")

        Wiz = self.env["purchase.ubl.import.wizard"]
        wiz = Wiz.new({})
        wiz._apply_xml_taxes_to_bill(bill, [{"product": product, "tax_percent": 0}])
        self.assertEqual(bill.invoice_line_ids.mapped("tax_ids"), original_taxes)

    def test_validate_receipt_no_picking_found_message(self):
        """validate_receipt=True but the order has no receipt yet (not confirmed)."""
        product = self.env["product.product"].create(
            {"name": "No Receipt Product", "default_code": "NORECEIPT", "is_storable": True, "purchase_ok": True}
        )
        po = self.po_model.create(
            {
                "partner_id": self.vendor.id,
                "company_id": self.company.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_qty": 1,
                            "price_unit": 5.0,
                            "name": product.name,
                            "product_uom_id": product.uom_id.id,
                            "date_planned": "2025-01-01 00:00:00",
                        },
                    )
                ],
            }
        )
        xml = _xml_invoice(
            order_ref=po.name,
            supplier_vat=self.vendor.vat,
            supplier_name=self.vendor.name,
            lines=[{"code": "NORECEIPT", "name": product.name, "qty": "1", "price": "5.0", "line_total": "5.0"}],
        )
        wiz = (
            self.env["purchase.ubl.import.wizard"]
            .with_context(active_model="purchase.order", active_id=po.id)
            .create(
                {
                    "data_file": b64encode(xml),
                    "filename": "noreceipt.xml",
                    "update_prices": False,
                    "create_bill": False,
                    "validate_receipt": True,
                    "create_missing_products": False,
                }
            )
        )
        wiz.action_import()
        self.assertIn("No receipt found to validate", wiz.log or "")

    def test_create_bill_skipped_message_without_order(self):
        """create_bill=True but no purchase order was resolved from context/order_ref."""
        xml = _xml_invoice(
            order_ref="NON-EXISTENT-PO-2",
            supplier_vat=self.vendor.vat,
            supplier_name=self.vendor.name,
            lines=[
                {"code": "STANDALONE-CODE-2", "name": "Standalone", "qty": "1", "price": "1.0", "line_total": "1.0"}
            ],
        )
        wiz = self.env["purchase.ubl.import.wizard"].create(
            {
                "data_file": b64encode(xml),
                "filename": "skipped_bill.xml",
                "update_prices": False,
                "create_bill": True,
                "validate_receipt": False,
                "create_missing_products": True,
            }
        )
        wiz.action_import()
        self.assertIn("Vendor bill creation skipped", wiz.log or "")

    def test_unmatched_line_on_order_without_lines_is_skipped(self):
        """An order with no lines yet: one XML line matches an existing product
        (added), one doesn't match and create_missing_products=False (skipped,
        reported as 'Unmatched lines in the order')."""
        matched_product = self.env["product.product"].create(
            {"name": "Matched Product", "default_code": "MATCH-1", "is_storable": True, "purchase_ok": True}
        )
        po = self.po_model.create(
            {
                "partner_id": self.vendor.id,
                "company_id": self.company.id,
            }
        )
        xml = _xml_invoice(
            order_ref=po.name,
            supplier_vat=self.vendor.vat,
            supplier_name=self.vendor.name,
            lines=[
                {"code": "MATCH-1", "name": matched_product.name, "qty": "1", "price": "1.0", "line_total": "1.0"},
                {"code": "NO-MATCH-1", "name": "Unmatched", "qty": "1", "price": "1.0", "line_total": "1.0"},
            ],
        )
        wiz = (
            self.env["purchase.ubl.import.wizard"]
            .with_context(active_model="purchase.order", active_id=po.id)
            .create(
                {
                    "data_file": b64encode(xml),
                    "filename": "partial_match.xml",
                    "update_prices": False,
                    "create_bill": False,
                    "validate_receipt": False,
                    "create_missing_products": False,
                }
            )
        )
        wiz.action_import()

        self.assertEqual(len(po.order_line), 1)
        self.assertEqual(po.order_line.product_id, matched_product)
        self.assertIn("Unmatched lines in the order", wiz.log or "")

    def test_action_view_vendor_bill_resolves_order_from_context(self):
        """When order_id isn't set on the wizard record itself, the method falls
        back to resolving the order from the active_model/active_id context."""
        po, _product = self._confirmed_po_with_line()
        po.action_create_invoice()
        Wiz = self.env["purchase.ubl.import.wizard"]
        wiz = Wiz.with_context(active_model="purchase.order", active_id=po.id).new({})
        # Simulate a wizard whose order_id was never populated (e.g. default_get
        # skipped it), so action_view_vendor_bill must fall back to the context.
        wiz.order_id = False
        action = wiz.action_view_vendor_bill()
        self.assertIsInstance(action, dict)

    def test_action_view_vendor_bill_without_any_order_closes(self):
        Wiz = self.env["purchase.ubl.import.wizard"]
        wiz = Wiz.new({})
        action = wiz.action_view_vendor_bill()
        self.assertEqual(action, {"type": "ir.actions.act_window_close"})
