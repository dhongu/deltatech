# © 2025 Deltatech
# See README.rst file on addons root folder for license details

import base64
from datetime import datetime
from io import BytesIO

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.misc import xlsxwriter


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # === Attachment helpers moved to purchase.order ===
    def _build_xlsx(self):
        """Build a combined XLSX for the current recordset of purchase orders (self)."""
        if not xlsxwriter:
            raise UserError(_("XlsxWriter is required to generate XLSX files."))
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet("Purchase Orders")
        # Formats
        head = workbook.add_format({"bold": True, "bg_color": "#D9E1F2"})
        num = workbook.add_format({"num_format": "0.00"})
        qty_fmt = workbook.add_format({"num_format": "0.00"})
        # Headers
        headers = [
            _("Order"),
            _("Origin"),
            _("Reference"),
            _("Product Code"),
            _("Product Description"),
            _("Quantity"),
            _("Price"),
        ]
        for idx, h in enumerate(headers):
            sheet.write(0, idx, h, head)
        row = 1
        for po in self:
            for line in po.order_line:
                default_code = line.product_id.default_code or ""
                name = line.name or (line.product_id.display_name or "")
                supplier = line.product_id.seller_ids.filtered(lambda s: s.partner_id == po.partner_id)
                if supplier:
                    default_code = supplier.product_code or default_code
                    name = supplier.product_name or name

                sheet.write(row, 0, po.name or "")
                sheet.write(row, 1, po.origin or "")
                sheet.write(row, 2, po.partner_ref or "")
                (sheet.write(row, 3, default_code),)
                (sheet.write(row, 4, name),)
                sheet.write_number(row, 5, line.product_qty or 0.0, qty_fmt)
                sheet.write_number(row, 6, line.price_unit or 0.0, num)
                row += 1
        # autosize simple
        for col, width in enumerate([18, 18, 50, 12, 12]):
            sheet.set_column(col, col, width)
        workbook.close()
        xlsx_data = output.getvalue()
        output.close()
        return xlsx_data

    def _prepare_attachments(self, attach_combined_xlsx=True, attach_order_pdfs=True):
        """Return a list of (filename, content_bytes, mimetype) for self POs."""
        attachments = []
        # 1) XLSX summary
        if attach_combined_xlsx:
            xlsx_data = self._build_xlsx()
            attachments.append(
                (
                    "purchase_orders_{}.xlsx".format(datetime.now().strftime("%Y%m%d_%H%M%S")),
                    xlsx_data,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            )

        # 2) PDF for each PO
        if attach_order_pdfs:
            # cauta toate pdf-urile din comenzi
            domain = [
                ("res_model", "=", "purchase.order"),
                ("res_id", "in", self.ids),
                ("mimetype", "=", "application/pdf"),
            ]
            existing_attachments = self.env["ir.attachment"].search(domain)
            for att in existing_attachments:
                attachments.append((att.name, att.raw, att.mimetype))

            if not existing_attachments:
                report = self.env.ref("purchase.action_report_purchase_order")
                # Render each PO separately to have distinct filenames
                for po in self:
                    pdf_bytes, _ = report._render_qweb_pdf(report.id, [po.id])
                    fname = "{}.pdf".format(po.name.replace("/", "-"))
                    attachments.append((fname, pdf_bytes, "application/pdf"))

        return attachments

    def action_compose_batch_email(self):
        """
        Open the standard mail.compose.message to send ONE email that aggregates
        all selected Purchase Orders (self). We use the existing transient wizard
        model as an aggregator record to which we attach the combined XLSX and
        individual PO PDFs, then open the composer on that record/template.
        """
        self = self.exists()
        if not self:
            return False
        # Ensure we have at least one PO
        pos = self
        # Create aggregator wizard record
        Wizard = self.env["purchase.send.xlsx.wizard"]
        template = self.env.ref("deltatech_purchase_mail.mail_template_purchase_send_xlsx", raise_if_not_found=False)
        wiz_vals = {
            "purchase_ids": [(6, 0, pos.ids)],
            "template_id": template.id if template else False,
        }
        # Prefill recipient if all vendors are the same and have an email
        partners = pos.mapped("partner_id")
        if len(partners) == 1 and partners.email:
            wiz_vals["email_to"] = partners.email
        else:
            raise UserError(_("You must select exactly one vendor to send the email to."))
        wiz = Wizard.create(wiz_vals)

        # Before composing, mark RFQs as sent by posting a message on each PO
        for po in pos:
            po.with_context(mark_rfq_as_sent=True).message_post(
                body=_("RFQ prepared for sending by email (batch compose)."),
                message_type="comment",
                subtype_xmlid="mail.mt_note",
            )

        # Build attachments using purchase.order helper
        attachments = pos._prepare_attachments(attach_combined_xlsx=True, attach_order_pdfs=True)
        attachment_ids = []
        for name, content, mimetype in attachments:
            att = self.env["ir.attachment"].create(
                {
                    "name": name,
                    "type": "binary",
                    "datas": base64.b64encode(content),
                    "mimetype": mimetype,
                    "res_model": wiz._name,
                    "res_id": wiz.id,
                }
            )
            attachment_ids.append(att.id)

        # Open the standard email composer on the wizard aggregator
        ctx = {
            "default_model": wiz._name,
            "default_res_ids": [wiz.id],
            "default_use_template": True,
            "default_template_id": wiz.template_id.id if wiz.template_id else False,
            "default_attachment_ids": [(6, 0, attachment_ids)],
            # Prefer email_to directly to allow free-form addresses
            "default_email_to": wiz.email_to or "",
            "default_partner_ids": [(6, 0, pos.mapped("partner_id").ids)],
            # Ensure downstream behaviors that look for this flag can still react
            "mark_rfq_as_sent": True,
        }
        return {
            "type": "ir.actions.act_window",
            "name": _("Compose Email"),
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "target": "new",
            "context": ctx,
        }
