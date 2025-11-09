# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class PurchaseSendXlsxWizard(models.TransientModel):
    _name = "purchase.send.xlsx.wizard"
    _description = "Send selected POs by email with XLSX and PDFs"

    purchase_ids = fields.Many2many(
        "purchase.order",
        string="Purchase Orders",
        help="Purchase Orders that will be included in the email.",
    )
    template_id = fields.Many2one(
        "mail.template",
        string="Email Template",
        domain=[("model", "=", "purchase.send.xlsx.wizard")],
        default=lambda self: self.env.ref(
            "deltatech_purchase_mail.mail_template_purchase_send_xlsx", raise_if_not_found=False
        ),
        help="Template used to compose the email. You can customize it in Settings > Technical > Email > Templates.",
    )
    email_to = fields.Char(
        string="To",
        help="Comma-separated list of recipient emails. If empty, email will be sent to the vendor email when all POs share the same vendor having an email.",
    )
    attach_combined_xlsx = fields.Boolean(string="Attach XLSX Summary", default=True)
    attach_order_pdfs = fields.Boolean(string="Attach Order PDFs", default=True)

    # Helpers have been moved to purchase.order. This class now only holds
    # the selected purchase orders and metadata for the email composer.
