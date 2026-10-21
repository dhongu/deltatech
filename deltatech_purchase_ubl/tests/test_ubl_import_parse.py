# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from base64 import b64encode

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from .test_ubl_import import UBL_NS, _xml_invoice


def _raw_invoice(line_body):
    """Minimal UBL invoice with one hand-written InvoiceLine body."""
    return f"""<inv:Invoice xmlns:inv="{UBL_NS["inv"]}" xmlns:cac="{UBL_NS["cac"]}" xmlns:cbc="{UBL_NS["cbc"]}">
        <cbc:ID>RAW-1</cbc:ID>
        <cac:InvoiceLine>{line_body}</cac:InvoiceLine>
    </inv:Invoice>""".encode()


@tagged("post_install", "-at_install")
class TestUblImportParse(TransactionCase):
    """Wizard side: XML detection/parsing, defaults, total check and preview."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.Wizard = cls.env["purchase.ubl.import.wizard"]
        cls.vendor = cls.env["res.partner"].create(
            {"name": "Parse Vendor SRL", "is_company": True, "vat": "RO10000001", "supplier_rank": 1}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Parse Product", "default_code": "PARSE-1", "is_storable": True, "purchase_ok": True}
        )

    def _order(self, qty=2.0, price=10.0):
        return self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "company_id": self.company.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": qty,
                            "price_unit": price,
                            "name": self.product.name,
                            "product_uom_id": self.product.uom_id.id,
                            "date_planned": "2025-01-01 00:00:00",
                            "tax_ids": [(5, 0, 0)],
                        },
                    )
                ],
            }
        )

    def _attach(self, order, name, content):
        return self.env["ir.attachment"].create(
            {
                "name": name,
                "datas": b64encode(content) if content else False,
                "mimetype": "application/xml",
                "res_model": "purchase.order",
                "res_id": order.id,
            }
        )

    # ------------------------------------------------------------------
    # UBL detection and parsing
    # ------------------------------------------------------------------
    def test_is_ubl_invoice_detection(self):
        self.assertTrue(self.Wizard._is_ubl_invoice(_xml_invoice()))
        self.assertFalse(self.Wizard._is_ubl_invoice(b"<not-xml"))
        self.assertFalse(self.Wizard._is_ubl_invoice(b"<foo><bar/></foo>"))
        # Another root (e.g. a CreditNote) is still accepted through the cbc:ID fallback
        other_root = f'<CreditNote xmlns:cbc="{UBL_NS["cbc"]}"><cbc:ID>CN-1</cbc:ID></CreditNote>'.encode()
        self.assertTrue(self.Wizard._is_ubl_invoice(other_root))

    def test_parse_invalid_xml_raises(self):
        with self.assertRaises(UserError):
            self.Wizard._parse_xml(b"<inv:Invoice")

    def test_parse_line_edge_values(self):
        """Unreadable numbers become 0, a charge (ChargeIndicator=true) is not a discount,
        an unreadable allowance amount is ignored and a non-GS1 standard id is no barcode."""
        content = _raw_invoice(
            """
            <cbc:InvoicedQuantity unitCode="C62">4</cbc:InvoicedQuantity>
            <cbc:LineExtensionAmount>n/a</cbc:LineExtensionAmount>
            <cac:AllowanceCharge>
                <cbc:ChargeIndicator>true</cbc:ChargeIndicator>
                <cbc:Amount>5</cbc:Amount>
            </cac:AllowanceCharge>
            <cac:AllowanceCharge>
                <cbc:ChargeIndicator>false</cbc:ChargeIndicator>
                <cbc:Amount>abc</cbc:Amount>
            </cac:AllowanceCharge>
            <cac:Price><cbc:PriceAmount>12,5</cbc:PriceAmount></cac:Price>
            <cac:Item>
                <cbc:Name>Edge Item</cbc:Name>
                <cac:StandardItemIdentification><cbc:ID schemeID="0088">5901234123457</cbc:ID></cac:StandardItemIdentification>
            </cac:Item>
            """
        )
        data = self.Wizard._parse_xml(content)
        line = data["lines"][0]
        self.assertEqual(line["price"], 12.5)
        self.assertEqual(line["line_total"], 0.0)
        self.assertEqual(line["discount"], 0.0)
        self.assertEqual(line["barcode"], "")
        self.assertEqual(data["currency"], "RON")
        self.assertEqual(data["payable_amount"], 0.0)

    def test_uom_from_ubl(self):
        self.assertEqual(self.Wizard._uom_from_ubl("KGM"), self.env.ref("uom.product_uom_kgm"))

    def test_actions_require_a_file(self):
        wizard = self.Wizard.new({})
        for method in (wizard.action_import, wizard.action_preview, wizard.action_confirm_import):
            with self.assertRaises(UserError):
                method()

    # ------------------------------------------------------------------
    # Defaults from the purchase order attachments
    # ------------------------------------------------------------------
    def test_default_get_takes_latest_ubl_attachment(self):
        order = self._order()
        ubl = _xml_invoice(order_ref=order.name)
        self._attach(order, "invoice.xml", ubl)
        self._attach(order, "empty.xml", b"")
        self._attach(order, "other.xml", b"<foo/>")

        defaults = self.Wizard.with_context(active_model="purchase.order", active_id=order.id).default_get(
            ["order_id", "data_file", "filename"]
        )
        self.assertEqual(defaults["order_id"], order.id)
        self.assertEqual(defaults["filename"], "invoice.xml")
        self.assertEqual(defaults["data_file"], b64encode(ubl))

    # ------------------------------------------------------------------
    # Total check
    # ------------------------------------------------------------------
    def test_total_check_warning_states(self):
        order = self._order(qty=2.0, price=10.0)
        self.assertEqual(order.amount_total, 20.0)

        no_order = self.Wizard.create({"data_file": b64encode(_xml_invoice(payable_amount="99"))})
        self.assertFalse(no_order.total_check_warning)

        invalid = self.Wizard.create({"data_file": b64encode(b"<broken"), "order_id": order.id})
        self.assertFalse(invalid.total_check_warning)

        matching = self.Wizard.create(
            {"data_file": b64encode(_xml_invoice(tax_exclusive_amount="20", payable_amount="20")), "order_id": order.id}
        )
        self.assertFalse(matching.total_check_warning)

        differing = self.Wizard.create(
            {
                "data_file": b64encode(
                    _xml_invoice(tax_exclusive_amount="20", tax_inclusive_amount="25", payable_amount="25")
                ),
                "order_id": order.id,
            }
        )
        self.assertIn("differs", differing.total_check_warning)

    def test_total_check_falls_back_to_untaxed_total(self):
        order = self._order(qty=2.0, price=10.0)
        check = self.Wizard._get_order_total_check(order, {"tax_exclusive_amount": 20.0, "lines": []})
        self.assertEqual(check["xml_amount"], 20.0)
        self.assertEqual(check["order_amount"], order.amount_untaxed)
        self.assertTrue(check["matches"])

    # ------------------------------------------------------------------
    # Preview without an order and manual override
    # ------------------------------------------------------------------
    def test_preview_without_order_and_manual_override(self):
        other = self.env["product.product"].create({"name": "Parse Other", "is_storable": True})
        xml = _xml_invoice(
            order_ref="",
            supplier_vat=self.vendor.vat,
            supplier_name=self.vendor.name,
            lines=[{"code": "PARSE-1", "name": "Parse Product", "qty": "1", "price": "5", "line_total": "5"}],
        )
        wizard = self.Wizard.create({"data_file": b64encode(xml)})
        wizard.action_preview()
        self.assertEqual(wizard.state, "preview")
        line = wizard.line_ids
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.match_type, "code")

        line.product_id = other
        line._onchange_product_id()
        self.assertEqual(line.match_type, "manual")

    def test_log_level_comes_from_the_caller_not_the_text(self):
        """A translated message no longer holds the English keywords: the level is passed."""
        html = self.Wizard._build_log_html([("danger", "Linii neasociate în comandă: X"), ("success", "Recepție")])
        self.assertIn("text-danger", html)
        self.assertIn("❌", html)
        self.assertIn("text-success", html)
        self.assertEqual(
            self.Wizard._build_log_text([("warning", "Avertisment"), "Vendor bill created: X"]),
            "⚠️ Avertisment\n✅ Vendor bill created: X",
        )

    def test_wizard_title(self):
        wizard = self.Wizard.new({"filename": "FMS-1.xml"})
        self.assertEqual(wizard.display_name, "Import Invoice: FMS-1.xml")
        self.assertEqual(wizard._reopen()["name"], "Import Invoice")

    def test_build_log_html_skips_blank_sub_lines(self):
        html = self.Wizard._build_log_html(["Created products (1):\n\nFirst <b>"])
        self.assertIn("First &lt;b&gt;", html)
        self.assertEqual(html.count("text-muted"), 1)
