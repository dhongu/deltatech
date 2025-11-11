# ©  2015-now Terrabit
# See README.rst file on addons root folder for license details

import html
from string import Template

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


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
        if followups:
            for followup in followups:
                for partner in partners:
                    partner_debit = 0.0
                    partner_all_debit = 0.0
                    partner_due_debit = 0.0
                    lang_id = self.env["res.lang"].search([("code", "=", partner.lang)])[0]
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
                        if followup.is_match(date_process):
                            # add invoice
                            invoices_to_process.append(invoice)
                        if invoice.payment_state in ["not_paid", "partial"]:
                            partner_all_debit += self.get_amount_residual(followup, invoice)
                            if invoice.invoice_date_due < fields.Date.today():
                                partner_due_debit += self.get_amount_residual(followup, invoice)
                    if invoices_to_process:
                        inv_currency = invoices_to_process[0].company_id.currency_id
                        if followup.use_customer_currency:
                            inv_currency = invoices_to_process[0].currency_id
                        # Do not send mail if total_due_debit is within configured margin
                        due_margin = followup.amount_margin
                        if abs(partner_due_debit) <= due_margin:
                            # Skip sending follow-up within the margin
                            partner.message_post(
                                body=(
                                    f"Follow-up not sent: total due debit ({partner_due_debit:,.2f} {inv_currency.name}) "
                                    f"is within the configured margin ({due_margin:,.2f} {inv_currency.name})."
                                ),
                                message_type="comment",
                                subtype_xmlid="mail.mt_note",
                            )
                            continue
                        invoices_content = ""
                        for invoice in invoices_to_process:
                            crt_row = Template(followup.invoice_html).substitute(
                                number=invoice.name,
                                payment_term_id=invoice.invoice_payment_term_id,
                                date_invoice=invoice.invoice_date.strftime(lang_id.date_format),
                                date_due=invoice.invoice_date_due.strftime(lang_id.date_format),
                                amount_untaxed=invoice.amount_untaxed,
                                amount_tax=invoice.amount_tax,
                                amount_total=invoice.amount_total,
                                amount_due=invoice.amount_residual,
                                currency=invoice.currency_id.name,
                            )
                            invoices_content += crt_row
                            partner_debit += invoice.amount_residual
                        email_values = {}
                        # Determine override partner recipient from system parameters, if any
                        override_partner_id = None
                        get_param = self.env["ir.config_parameter"].sudo().get_param
                        override_value = safe_eval(get_param("followup.override_partner_id", "False"))
                        if override_value:
                            try:
                                override_partner_id = int(override_value)
                            except ValueError:
                                override_partner_id = None
                            # todo: de corectat metoda de transmitere email
                        mail_values = followup.mail_template.with_context(
                            template_preview_lang=partner.lang
                        )._generate_template(
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
                        body = body.replace("$total_debit", f"{partner_debit:,.2f}")
                        body = body.replace("$total_all_debit", f"{partner_all_debit:,.2f}")
                        body = body.replace("$total_due_debit", f"{partner_due_debit:,.2f}")
                        body = body.replace("$currency", inv_currency.name)
                        if "[invoices]" in followup.mail_template.body_html:
                            body = body.replace("[invoices]", invoices_content)
                        body = html.unescape(body)
                        email_values = {
                            "body_html": body,
                        }
                        # Always override recipients when a valid system parameter is set
                        if override_partner_id:
                            email_values["recipient_ids"] = [(6, 0, [override_partner_id])]
                        followup.mail_template.send_mail(partner.id, False, False, email_values)
