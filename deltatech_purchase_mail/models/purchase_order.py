# © 2025 Deltatech
# See README.rst file on addons root folder for license details

import base64
from datetime import datetime
from io import BytesIO

import xlsxwriter

from odoo import models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # === Attachment helpers moved to purchase.order ===
    def _build_xlsx(self):
        """Build a combined XLSX for the current recordset of purchase orders (self)."""
        if not xlsxwriter:
            raise UserError(self.env._("XlsxWriter is required to generate XLSX files."))
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet("Purchase Orders")
        # Formats
        head = workbook.add_format({"bold": True, "bg_color": "#D9E1F2"})
        num = workbook.add_format({"num_format": "0.00"})
        qty_fmt = workbook.add_format({"num_format": "0.00"})
        # Headers
        headers = [
            self.env._("Order"),
            self.env._("Product Code"),
            self.env._("Product Description"),
            self.env._("Quantity"),
            self.env._("Price"),
        ]
        for idx, h in enumerate(headers):
            sheet.write(0, idx, h, head)
        row = 1
        for po in self:
            for line in po.order_line:
                sheet.write(row, 0, po.name or "")
                sheet.write(row, 1, line.product_id.default_code or "")
                sheet.write(row, 2, line.name or (line.product_id.display_name or ""))
                sheet.write_number(row, 3, line.product_qty or 0.0, qty_fmt)
                # Unit price: taxes excluded price_unit
                sheet.write_number(row, 4, line.price_unit or 0.0, num)
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
        Nothing is posted and no state changes here: when the email is really sent,
        the composer calls `_log_sent_email` (see mail_compose_message.py).
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
            raise UserError(self.env._("You must select exactly one vendor to send the email to."))
        wiz = Wizard.create(wiz_vals)

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
        }
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Compose Email"),
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "target": "new",
            "context": ctx,
        }

    def _log_sent_email(self, message):
        """Record the batch email on each order (self) and mark the RFQs as sent.

        The composer runs on the aggregator wizard, so the message is not on the
        orders. Each order gets a note with the same body and its own attachments
        (the summary and the PDF of the order, not the PDFs of the other orders).
        """
        pdf_names = {po.id: "{}.pdf".format((po.name or "").replace("/", "-")) for po in self}
        for po in self:
            other_pdfs = {name for po_id, name in pdf_names.items() if po_id != po.id}
            attachments = message.attachment_ids.filtered(lambda att, other_pdfs=other_pdfs: att.name not in other_pdfs)
            copies = self.env["ir.attachment"]
            for att in attachments:
                copies |= att.copy({"res_model": po._name, "res_id": po.id})
            po.with_context(mark_rfq_as_sent=True).message_post(
                body=message.body,
                subject=message.subject,
                message_type="comment",
                subtype_xmlid="mail.mt_note",
                attachment_ids=copies.ids,
            )
