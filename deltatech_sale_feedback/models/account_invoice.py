# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    @api.model
    def cron_request_feedback(self):
        days_request_feedback = self.env["ir.config_parameter"].sudo().get_int("sale.days_request_feedback", 3)
        invoice_date = date.today() + relativedelta(days=-days_request_feedback)
        domain = [
            ("move_type", "=", "out_invoice"),
            ("state", "=", "posted"),
            ("invoice_date", "=", invoice_date),
            ("company_id.sale_feedback", "=", True),
        ]
        invoices = self.env["account.move"].search(domain)
        invoices.request_feedback()

    def request_feedback(self):
        default_template = self.env.ref("deltatech_sale_feedback.mail_template_sale_feedback")
        for invoice in self.filtered(lambda i: i.move_type == "out_invoice"):
            template = invoice.company_id.sale_feedback_template_id or default_template
            invoice.with_context(web_base_url=invoice.company_id.website).message_post_with_source(
                template,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
                email_layout_xmlid="mail.mail_notification_light",
                force_send=True,
            )

    def get_base_url(self):
        # linkurile de rating din e-mail duc pe website-ul companiei, dacă e setat
        web_base_url = self.env.context.get("web_base_url")
        if web_base_url:
            return web_base_url.rstrip("/")
        return super().get_base_url()


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    def rating_get_access_token(self):
        rating = self.env["rating.rating"].create(
            {
                "res_model_id": self.env["ir.model"]._get_id("product.template"),
                "res_id": self.product_id.product_tmpl_id.id,
                "partner_id": self.move_id.partner_id.id,
                "is_internal": False,
            }
        )
        return rating.access_token
