# ©  2015-now Terrabit
# See README.rst file on addons root folder for license details

import html
import logging
from string import Template

from odoo import api, fields, models
from odoo.tools.misc import formatLang
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class FollowupSendWizard(models.TransientModel):
    _name = "followup.send.wizard"
    _description = "Followup Send Wizard"

    def get_amount_residual(self, followup, invoice):
        if followup.use_customer_currency:
            if invoice.move_type == "out_refund":
                return -1 * invoice.amount_residual
            else:
                return invoice.amount_residual
        else:
            return invoice.amount_residual_signed

    @api.model
    def run_followup(self, codes=False):
        # run by cron job
        if not codes:
            followups = self.env["account.invoice.followup"].search([])
        else:
            domain = [("code", "in", codes)]
            followups = self.env["account.invoice.followup"].search(domain)
        partners = self.env["res.partner"].search([("send_followup", "=", True)])
        for followup in followups:
            for partner in partners:
                # one partner with bad data must not stop the followups of the others
                try:
                    with self.env.cr.savepoint():
                        self._run_followup_partner(followup, partner)
                except Exception as exc:  # pylint: disable=broad-except
                    _logger.exception("Followup %s failed for partner %s", followup.display_name, partner.id)
                    partner.message_post(
                        body=self.env._(
                            "Followup %(followup)s failed and was not sent: %(error)s",
                            followup=followup.display_name,
                            error=str(exc),
                        ),
                        message_type="comment",
                        subtype_xmlid="mail.mt_note",
                    )

    def _run_followup_partner(self, followup, partner):
        partner_debit = 0.0
        partner_all_debit = 0.0
        partner_due_debit = 0.0
        lang_id = (
            self.env["res.lang"]._lang_get(partner.lang)
            or self.env["res.lang"]._lang_get(self.env.lang)
            or self.env["res.lang"].search([], limit=1)
        )

        def format_amount(value, lang=lang_id):
            # amounts in the language of the partner, ex. 2.380,00 for ro_RO
            return lang.format("%.2f", value, grouping=True)

        domain = [
            ("partner_id", "=", partner.id),
            ("state", "in", ["posted"]),
        ]
        if followup.only_open:
            domain = [
                ("partner_id", "=", partner.id),
                ("state", "in", ["posted"]),
                ("payment_state", "in", ["not_paid", "partial"]),
            ]
        if followup.with_refunds:
            domain.append(("move_type", "in", ["out_invoice", "out_refund"]))
        else:
            domain.append(("move_type", "=", "out_invoice"))
        invoices = self.env["account.move"].search(domain)
        invoices_to_process = []
        for invoice in invoices:
            if followup.date_field == "Invoice date":
                date_process = invoice.invoice_date
            else:
                date_process = invoice.invoice_date_due
            if date_process and followup.is_match(date_process):
                # add invoice
                invoices_to_process.append(invoice)
            if invoice.payment_state in ["not_paid", "partial"]:
                partner_all_debit += self.get_amount_residual(followup, invoice)
                if invoice.invoice_date_due and invoice.invoice_date_due < fields.Date.today():
                    partner_due_debit += self.get_amount_residual(followup, invoice)
        if invoices_to_process:
            inv_currency = invoices_to_process[0].company_id.currency_id
            if followup.use_customer_currency:
                inv_currency = invoices_to_process[0].currency_id
            # Do not send mail if the total of the invoices to send is within configured margin
            invoices_amount = sum(self.get_amount_residual(followup, inv) for inv in invoices_to_process)
            due_margin = followup.amount_margin
            # a negative total (credit notes over invoices) is not a debit to remind about
            if invoices_amount <= due_margin:
                # Skip sending followup within the margin
                partner.message_post(
                    body=self.env._(
                        "Followup not sent: total of the invoices to send (%(amount)s) "
                        "is within the configured margin (%(margin)s).",
                        amount=formatLang(self.env, invoices_amount, currency_obj=inv_currency),
                        margin=formatLang(self.env, due_margin, currency_obj=inv_currency),
                    ),
                    message_type="comment",
                    subtype_xmlid="mail.mt_note",
                )
                return
            invoices_content = ""
            for invoice in invoices_to_process:
                # credit notes are shown and summed with a negative sign
                sign = -1 if invoice.move_type == "out_refund" else 1
                crt_row = Template(followup.invoice_html or "").substitute(
                    number=invoice.name,
                    payment_term_id=invoice.invoice_payment_term_id.name or "",
                    date_invoice=invoice.invoice_date.strftime(lang_id.date_format),
                    date_due=invoice.invoice_date_due.strftime(lang_id.date_format),
                    amount_untaxed=format_amount(sign * invoice.amount_untaxed),
                    amount_tax=format_amount(sign * invoice.amount_tax),
                    amount_total=format_amount(sign * invoice.amount_total),
                    amount_due=format_amount(sign * invoice.amount_residual),
                    currency=invoice.currency_id.name,
                )
                invoices_content += crt_row
                partner_debit += self.get_amount_residual(followup, invoice)
            # email_values = {}
            override_partner_id = None
            get_str = self.env["ir.config_parameter"].sudo().get_str
            override_value = safe_eval(get_str("followup.override_partner_id", "False"))
            if override_value:
                try:
                    override_partner_id = int(override_value)
                except ValueError:
                    override_partner_id = None

                # todo: de corectat metoda de transmitere email
            mail_values = followup.mail_template.with_context(template_preview_lang=partner.lang)._generate_template(
                [partner.id],
                [
                    "subject",
                    "body_html",
                    "email_from",
                    "email_to",
                    "partner_to",
                    "email_cc",
                    "reply_to",
                    "scheduled_date",
                ],
            )
            new_body = mail_values[partner.id]["body_html"]
            body = new_body.replace("${object.name}", partner.name)
            body = body.replace("$total_debit", format_amount(partner_debit))
            body = body.replace("$total_all_debit", format_amount(partner_all_debit))
            body = body.replace("$total_due_debit", format_amount(partner_due_debit))
            body = body.replace("$currency", inv_currency.name)
            if "[invoices]" in followup.mail_template.body_html:
                body = body.replace("[invoices]", invoices_content)
            body = html.unescape(body)
            email_values = {
                "body_html": body,
            }
            if override_partner_id:
                email_values["recipient_ids"] = [(6, 0, [override_partner_id])]
            followup.mail_template.send_mail(partner.id, False, False, email_values)
