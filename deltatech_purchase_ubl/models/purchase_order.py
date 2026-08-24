# © 2025 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

import base64

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _process_attachments_for_post(self, attachments, attachment_ids, message_values):
        # Run super first to let core create attachments/links properly
        res = super()._process_attachments_for_post(attachments, attachment_ids, message_values)

        # Feature toggle
        ICP = self.env["ir.config_parameter"].sudo()
        enabled = ICP.get_param("deltatech_purchase_ubl.auto_import", default="True")
        if str(enabled).lower() not in ("true", "1", "yes", "y"):
            return res

        # Process only for this recordset
        for order in self:
            for attachment in self.env["ir.attachment"].sudo().browse(attachment_ids):
                # Only attachments linked to current PO
                if attachment.res_model != "purchase.order" or attachment.res_id != order.id:
                    continue
                # Consider only XML files
                name_l = (attachment.name or "").lower()
                mimetype = (attachment.mimetype or "").lower()
                if not (name_l.endswith(".xml") or mimetype in ("application/xml", "text/xml")):
                    continue
                if not attachment.datas:
                    continue
                # Validate UBL using wizard helper
                try:
                    xml_bytes = base64.b64decode(attachment.datas)
                except Exception:
                    continue
                wiz_tmp = self.env["purchase.ubl.import.wizard"].new({})
                try:
                    is_ubl = bool(wiz_tmp._is_ubl_invoice(xml_bytes))
                except Exception:
                    is_ubl = False
                if not is_ubl:
                    continue

                # Run the wizard headlessly in PO context.
                # `purchase_ubl_no_new_products` in context lets an automated caller (no human
                # reviewing the import as it happens) opt out of silent product creation when
                # the source document doesn't identify the product unambiguously (missing
                # supplier code, ambiguous name match) — see l10n_ro_message_spv_purchase,
                # which sets this when it auto-attaches an SPV XML on a freshly created PO.
                create_missing_products = not self.env.context.get("purchase_ubl_no_new_products")
                try:
                    wiz = self.env["purchase.ubl.import.wizard"].create(
                        {
                            "data_file": attachment.datas,
                            "filename": attachment.name,
                            "order_id": order.id,
                            "update_prices": True,
                            "validate_receipt": True,
                            "create_bill": True,
                            "create_missing_products": create_missing_products,
                        }
                    )
                    wiz = wiz.with_context(active_model="purchase.order", active_id=order.id)
                    wiz.action_import()
                    # Optional: post log on PO for traceability
                    if wiz.log:
                        order.message_post(body=wiz.log)
                except Exception:
                    # Swallow exceptions to not break message posting; errors will be visible in server logs
                    continue

        return res
