# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, models
from odoo.tools.safe_eval import safe_eval


class AccountInvoice(models.Model):
    _inherit = "account.move"

    @api.model
    def cron_request_feedback(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        days_request_feedback = safe_eval(get_param("sale.days_request_feedback", "3"))
        invoice_date = date.today() + relativedelta(days=-days_request_feedback)
        domain = [("move_type", "=", "out_invoice"), ("invoice_date", "=", invoice_date)]
        invoices = self.env["account.move"].search(domain)
        invoices.request_feedback()

    def request_feedback(self):
        res_id = "deltatech_sale_feedback.mail_template_sale_feedback"
        template_id = self.env["ir.model.data"].xmlid_to_res_id(res_id, raise_if_not_found=True)
        for invoice in self.filtered(lambda i: i.move_type == "out_invoice"):
            message_post = invoice.with_context(force_send=True).message_post_with_template

            message_post(template_id, composition_mode="comment", email_layout_xmlid="mail.mail_notification_light")


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    def rating_get_access_token(self):

        model_product_template = self.env["ir.model"].search([("model", "=", "product.template")], limit=1)
        rating = self.env["rating.rating"].create(
            {
                "res_model_id": model_product_template.id,
                "res_id": self.product_id.product_tmpl_id.id,
                "partner_id": self.move_id.partner_id.id,
                "is_internal": False,
            }
        )
        return rating.access_token
