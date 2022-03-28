# ©  2015-now Terrabit
# See README.rst file on addons root folder for license details

from string import Template

from odoo import api, fields, models
from odoo.tools import float_compare


class FollowupSend(models.TransientModel):
    _name = "followup.send.wizard"
    _description = "Followup Send Wizard"

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
                    lang_id = self.env["res.lang"].search([("code", "=", partner.lang)])[0]
                    domain = [
                        ("partner_id", "=", partner.id),
                        ("type", "=", "out_invoice"),
                        ("state", "in", ["posted"]),
                    ]
                    if followup.only_open:
                        domain = [
                            ("partner_id", "=", partner.id),
                            ("type", "=", "out_invoice"),
                            ("state", "in", ["posted"]),
                            ("invoice_payment_state", "=", "not_paid"),
                        ]
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
                    if invoices_to_process:
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
                            )
                            invoices_content += crt_row
                            partner_debit += invoice.amount_residual
                        email_values = {}
                        if "[invoices]" in followup.mail_template.body_html:
                            mail_values = followup.mail_template.with_context(
                                template_preview_lang=partner.lang
                            ).generate_email(partner.id)
                            new_body = mail_values["body"]
                            override_id = (
                                self.env["ir.config_parameter"]
                                .sudo()
                                .get_param("followup.override_partner_id", default=False)
                            )
                            if override_id:
                                try:
                                    partner_id = int(override_id)
                                except ValueError:
                                    partner_id = partner.id
                            else:
                                partner_id = partner.id
                            body = new_body.replace("[invoices]", invoices_content)
                            body = body.replace("${object.name}", partner.name)
                            body = body.replace("$total_debit", "{:,.2f}".format(partner_debit))
                            email_values = {
                                "body_html": body,
                                "recipient_ids": [(4, partner_id)],
                            }
                        followup.mail_template.send_mail(partner.id, False, False, email_values)

    @api.model
    def run_followup_aml(self, codes=False):
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
                    partner.env.cr.execute(
                        """SELECT l.partner_id, p.name, p.vat, a.user_type_id, t.type, l.debit,l.credit
                                                            FROM account_move_line l
                                                            LEFT JOIN account_account a ON (l.account_id=a.id)
                                                            LEFT JOIN res_partner p ON (l.partner_id=p.id)
                                                            LEFT JOIN account_account_type t ON (a.user_type_id=t.id)
                                                            WHERE t.type IN ('receivable','payable')
                                                            AND l.parent_state = 'posted'
                                                            AND l.full_reconcile_id IS NULL
                                                            AND l.partner_id = %s
                                                            AND l.date <= %s
                                                            """,
                        (partner.id, fields.Date.today()),
                    )
                    partner_moves = self.env.cr.fetchall()
                    debit_payable = 0.0
                    credit_payable = 0.0
                    debit_receivable = 0.0
                    credit_receivable = 0.0
                    for move in partner_moves:
                        if move[4] == "payable":
                            debit_payable += move[5]
                            credit_payable += move[6]
                        elif move[4] == "receivable":
                            debit_receivable += move[5]
                            credit_receivable += move[6]

                    if float_compare(debit_receivable, credit_receivable, precision_digits=2) == 1:
                        mail_values = followup.mail_template.with_context(
                            template_preview_lang=partner.lang
                        ).generate_email(partner.id)
                        body = mail_values["body"]
                        override_id = (
                            self.env["ir.config_parameter"]
                            .sudo()
                            .get_param("followup.override_partner_id", default=False)
                        )
                        if override_id:
                            try:
                                partner_id = int(override_id)
                            except ValueError:
                                partner_id = partner.id
                        else:
                            partner_id = partner.id
                        body = body.replace("$total_debit", "{:,.2f}".format(debit_receivable - credit_receivable))
                        email_values = {
                            "body_html": body,
                            "recipient_ids": [(4, partner_id)],
                        }
                        followup.mail_template.send_mail(partner.id, False, False, email_values)
