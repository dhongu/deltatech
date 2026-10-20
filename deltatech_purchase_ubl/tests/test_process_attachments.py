# © 2025 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

from base64 import b64encode
from textwrap import dedent
from unittest.mock import patch

from odoo.exceptions import UserError
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

    def test_auto_import_does_not_create_product_with_no_new_products_context(self):
        """Ticket #9315: an automated caller (e.g. l10n_ro_message_spv_purchase attaching an
        SPV XML on a PO created before the vendor bill) must be able to opt out of silent
        product creation when the invoice line has no supplier code and no exact name match —
        the line should be reported as unmatched instead of spawning a duplicate product."""
        xml = _xml_invoice(order_ref=self.po.name)
        att = self.env["ir.attachment"].create(
            {
                "name": "invoice_attach_no_new_products.xml",
                "datas": b64encode(xml),
                "mimetype": "application/xml",
                "res_model": "purchase.order",
                "res_id": self.po.id,
            }
        )

        products_before = self.env["product.product"].search_count([])
        self.po.with_context(purchase_ubl_no_new_products=True)._process_attachments_for_post([], [att.id], {})

        self.assertFalse(self.po.order_line, "No order line should be created when no product could be matched")
        self.assertEqual(
            self.env["product.product"].search_count([]),
            products_before,
            "No new product should have been created",
        )

    def test_unmatched_line_schedules_activity_instead_of_silent_chatter_note(self):
        """Tichet #9287 (continuare): a plain chatter note is easy to miss among the SPV
        cron's other automated traffic — an unmatched line (or a total mismatch) must
        surface as a to-do activity on the purchase order, not just as log text."""
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "company_id": self.company.id,
                "date_order": "2025-01-01 00:00:00",
                "partner_ref": "ATT-EXT-PO-REF-WARN",
            }
        )
        xml = _xml_invoice(order_ref=po.name)
        att = self.env["ir.attachment"].create(
            {
                "name": "invoice_attach_warning.xml",
                "datas": b64encode(xml),
                "mimetype": "application/xml",
                "res_model": "purchase.order",
                "res_id": po.id,
            }
        )

        po.with_context(purchase_ubl_no_new_products=True)._process_attachments_for_post([], [att.id], {})

        activities = po.activity_ids.filtered(lambda a: a.summary == "SPV import needs review")
        self.assertTrue(activities, "An unmatched line must schedule a review activity on the PO")

        # Reprocessing the same attachment (the SPV cron is known to retry) must not pile up
        # duplicate activities.
        po.with_context(purchase_ubl_no_new_products=True)._process_attachments_for_post([], [att.id], {})
        activities_after = po.activity_ids.filtered(lambda a: a.summary == "SPV import needs review")
        self.assertEqual(len(activities_after), 1, "Reprocessing must not create duplicate review activities")

    def test_matched_import_does_not_schedule_activity(self):
        """A clean import (everything matched, totals agree) must not create noise."""
        po = self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "company_id": self.company.id,
                "date_order": "2025-01-01 00:00:00",
                "partner_ref": "ATT-EXT-PO-REF-CLEAN",
            }
        )
        existing_product = self.env["product.product"].create({"name": "Matched Product", "type": "consu"})
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.vendor.id,
                "product_tmpl_id": existing_product.product_tmpl_id.id,
                "product_id": existing_product.id,
                "product_code": "VEND-ATT-NEW",
            }
        )
        xml = _xml_invoice(order_ref=po.name)
        att = self.env["ir.attachment"].create(
            {
                "name": "invoice_attach_clean.xml",
                "datas": b64encode(xml),
                "mimetype": "application/xml",
                "res_model": "purchase.order",
                "res_id": po.id,
            }
        )

        po._process_attachments_for_post([], [att.id], {})

        self.assertFalse(
            po.activity_ids.filtered(lambda a: a.summary == "SPV import needs review"),
            "A fully matched import must not schedule a review activity",
        )

    def _new_po(self, ref):
        return self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "company_id": self.company.id,
                "date_order": "2025-01-01 00:00:00",
                "partner_ref": ref,
            }
        )

    def _attachment(self, po, name, content, mimetype="application/xml"):
        return self.env["ir.attachment"].create(
            {
                "name": name,
                "datas": b64encode(content) if content else False,
                "mimetype": mimetype,
                "res_model": "purchase.order",
                "res_id": po.id,
            }
        )

    def test_auto_import_disabled_by_parameter(self):
        po = self._new_po("ATT-DISABLED")
        att = self._attachment(po, "disabled.xml", _xml_invoice(order_ref=po.name))
        self.env["ir.config_parameter"].sudo().set_param("deltatech_purchase_ubl.auto_import", "False")
        po._process_attachments_for_post([], [att.id], {})
        self.assertFalse(po.order_line, "Nothing is imported when the feature is switched off")

    def test_auto_import_skips_unrelated_attachments(self):
        """Attachments of another order, non-XML files, empty files and non-UBL XML are ignored."""
        po = self._new_po("ATT-SKIP")
        other_po = self._new_po("ATT-SKIP-OTHER")
        attachments = (
            self._attachment(other_po, "other_order.xml", _xml_invoice(order_ref=other_po.name))
            | self._attachment(po, "notes.txt", b"plain text", mimetype="text/plain")
            | self._attachment(po, "empty.xml", b"")
            | self._attachment(po, "not_ubl.xml", b"<foo/>")
        )
        po._process_attachments_for_post([], attachments.ids, {})
        self.assertFalse(po.order_line)
        self.assertFalse(other_po.order_line, "Only attachments of the posting order are processed")

    def test_auto_import_ubl_check_error_is_ignored(self):
        po = self._new_po("ATT-CHECK-ERR")
        att = self._attachment(po, "check_error.xml", _xml_invoice(order_ref=po.name))
        wizard_cls = type(self.env["purchase.ubl.import.wizard"])
        with patch.object(wizard_cls, "_is_ubl_invoice", side_effect=ValueError("boom")):
            po._process_attachments_for_post([], [att.id], {})
        self.assertFalse(po.order_line)

    def test_auto_import_error_does_not_break_posting(self):
        """An import error is swallowed: the message is still posted, nothing is imported."""
        po = self._new_po("ATT-IMPORT-ERR")
        att = self._attachment(po, "import_error.xml", _xml_invoice(order_ref=po.name))
        wizard_cls = type(self.env["purchase.ubl.import.wizard"])
        with patch.object(wizard_cls, "action_import", side_effect=UserError("Import failed")):
            po._process_attachments_for_post([], [att.id], {})
        self.assertFalse(po.order_line)
        self.assertFalse(po.activity_ids)

    def test_unmatched_line_defers_vendor_bill(self):
        """An unattended import must not create a vendor bill that misses the unmatched lines."""
        po = self._new_po("ATT-DEFER-BILL")
        product = self.env["product.product"].create({"name": "Defer Matched Product", "type": "consu"})
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.vendor.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "product_id": product.id,
                "product_code": "VEND-DEFER-OK",
            }
        )
        self.env["purchase.order.line"].create(
            {"order_id": po.id, "product_id": product.id, "product_qty": 2, "price_unit": 10.0}
        )
        po.button_confirm()
        lines = [
            {"code": "VEND-DEFER-OK", "name": "Matched", "qty": "2", "price": "10.00", "line_total": "20.00"},
            {
                "code": "VEND-DEFER-NONE",
                "name": "Nowhere To Be Found",
                "qty": "1",
                "price": "5.00",
                "line_total": "5.00",
            },
        ]
        att = self._attachment(
            po, "defer_bill.xml", _xml_invoice(order_ref=po.name, invoice_id="INV-DEFER", lines=lines)
        )
        wizard_cls = type(self.env["purchase.ubl.import.wizard"])
        with patch.object(wizard_cls, "_on_unmatched_lines", autospec=True) as hook:
            po.with_context(purchase_ubl_no_new_products=True)._process_attachments_for_post([], [att.id], {})
        self.assertFalse(po.invoice_ids, "No vendor bill while a line of the invoice is unmatched")
        self.assertIn("unmatched", po.message_ids[0].body)
        self.assertEqual(hook.call_args.args[4], [1], "The hook receives the index of the unmatched line")

    def test_skip_auto_import_context(self):
        """A caller that opens the import wizard itself attaches the XML without importing."""
        po = self._new_po("ATT-SKIP-AUTO")
        att = self._attachment(po, "skip_auto.xml", _xml_invoice(order_ref=po.name))
        po.with_context(purchase_ubl_skip_auto_import=True)._process_attachments_for_post([], [att.id], {})
        self.assertFalse(po.order_line)

    def _preview(self, po, lines):
        xml = _xml_invoice(order_ref=po.name, invoice_id=f"INV-{po.name}", lines=lines)
        wizard = (
            self.env["purchase.ubl.import.wizard"]
            .with_context(active_model="purchase.order", active_id=po.id)
            .create({"data_file": b64encode(xml), "filename": "preview.xml", "order_id": po.id})
        )
        wizard.action_preview()
        return wizard

    def test_preview_unmatched_line_is_ignored_by_default(self):
        po = self._new_po("ATT-PREVIEW-IGNORE")
        known = self.env["product.product"].create({"name": "Preview Known", "type": "consu"})
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.vendor.id,
                "product_tmpl_id": known.product_tmpl_id.id,
                "product_id": known.id,
                "product_code": "PRV-KNOWN",
            }
        )
        lines = [
            {"code": "PRV-KNOWN", "name": "Preview Known", "qty": "1", "price": "4", "line_total": "4"},
            {"code": "PRV-NEW", "name": "Preview Nowhere", "qty": "2", "price": "5", "line_total": "10"},
        ]
        wizard = self._preview(po, lines)
        self.assertEqual(wizard.line_ids.mapped("line_action"), ["product", "skip"])
        products_before = self.env["product.product"].search_count([])
        wizard.action_confirm_import()
        self.assertEqual(po.order_line.product_id, known)
        self.assertEqual(self.env["product.product"].search_count([]), products_before)

    def test_preview_create_product_on_request(self):
        po = self._new_po("ATT-PREVIEW-CREATE")
        lines = [{"code": "PRV-CREATE", "name": "Preview Created", "qty": "2", "price": "5", "line_total": "10"}]
        wizard = self._preview(po, lines)
        wizard.line_ids.line_action = "create"
        wizard.action_confirm_import()
        self.assertEqual(po.order_line.product_id.name, "Preview Created")
        self.assertEqual(po.order_line.product_qty, 2)
        action = wizard.action_open_order()
        self.assertEqual((action["res_model"], action["res_id"]), ("purchase.order", po.id))

    def _known_product(self, code):
        product = self.env["product.product"].create({"name": f"Clean {code}", "type": "consu"})
        self.env["product.supplierinfo"].create(
            {
                "partner_id": self.vendor.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "product_id": product.id,
                "product_code": code,
            }
        )
        return product

    def _wizard(self, po, lines):
        xml = _xml_invoice(order_ref=po.name, invoice_id=f"INV-{po.name}", lines=lines)
        return (
            self.env["purchase.ubl.import.wizard"]
            .with_context(active_model="purchase.order", active_id=po.id)
            .create({"data_file": b64encode(xml), "filename": "clean.xml", "order_id": po.id, "create_bill": False})
        )

    def test_clean_invoice_imports_without_preview(self):
        po = self._new_po("ATT-CLEAN")
        product = self._known_product("CLEAN-1")
        lines = [{"code": "CLEAN-1", "name": "x", "qty": "2", "price": "10", "line_total": "20", "tax": "0"}]
        action = self._wizard(po, lines).action_preview_or_import()
        self.assertEqual(action["tag"], "display_notification")
        self.assertEqual(action["params"]["next"]["res_id"], po.id)
        # the web client needs `views` on the next action: it is not cleaned up by the server
        self.assertEqual(action["params"]["next"]["views"], [[False, "form"]])
        self.assertRecordValues(po.order_line, [{"product_id": product.id, "product_qty": 2, "price_unit": 10}])

    def test_total_mismatch_rolls_back_and_opens_preview(self):
        po = self._new_po("ATT-CLEAN-TOTAL")
        self._known_product("CLEAN-2")
        lines = [{"code": "CLEAN-2", "name": "x", "qty": "2", "price": "10", "line_total": "25", "tax": "0"}]
        wizard = self._wizard(po, lines)
        action = wizard.action_preview_or_import()
        self.assertEqual(action["res_model"], "purchase.ubl.import.wizard")
        self.assertEqual(wizard.state, "preview")
        self.assertFalse(po.order_line, "the import is rolled back for review")

    def test_unmatched_line_opens_preview(self):
        po = self._new_po("ATT-CLEAN-UNMATCHED")
        self._known_product("CLEAN-3")
        lines = [
            {"code": "CLEAN-3", "name": "x", "qty": "1", "price": "10", "line_total": "10", "tax": "0"},
            {"code": "CLEAN-NONE", "name": "Nowhere", "qty": "1", "price": "5", "line_total": "5", "tax": "0"},
        ]
        wizard = self._wizard(po, lines)
        self.assertEqual(wizard.action_preview_or_import()["res_model"], "purchase.ubl.import.wizard")
        self.assertFalse(po.order_line)
