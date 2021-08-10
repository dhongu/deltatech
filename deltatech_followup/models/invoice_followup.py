# ©  2015-now Terrabit
# See README.rst file on addons root folder for license details

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class InvoiceFollowup(models.Model):
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _name = "account.invoice.followup"
    _description = "Invoice Followup"

    active = fields.Boolean(default=True)
    name = fields.Char("Name", help="Name of the followup")
    date_field = fields.Selection(
        [("Invoice date", "Invoice date"), ("Due date", "Due date")],
        default="Due date",
        string="Date field to use",
        help="The date field from the invoices from which the " "send date will be computed",
    )
    relative_days = fields.Integer(
        "Days from",
        help="Relative days from date field. Can be negative if you want to "
        "send this followup before the given date",
    )
    match = fields.Selection(
        [("=", "Equal"), (">=", "Greater or equal")],
        default="=",
        string="Comparator",
        help="Comparator operator. If equal, only the invoices with the "
        "exact date will be processed. If greater or equal, all the"
        "invoices with date grater or equal with the computed date"
        "will be processed",
    )
    only_open = fields.Boolean(
        "Only open invoices", default=True, help="Only open (unpaid) invoices will be " "processed"
    )
    invoice_html = fields.Html(
        "Invoices placeholder",
        help="This code will be inserted into the mail, replacing the"
        "[invoices] key string. The following placeholders can"
        "be used:\n"
        "$number=invoice.number,\n"
        "$payment_term_id=invoice.payment_term_id,\n"
        "$date_invoice=invoice.date_invoice,\n"
        "$date_due=invoice.date_due,\n"
        "$amount_untaxed=invoice.amount_untaxed,\n"
        "$amount_tax=invoice.amount_tax,\n"
        "$amount_total=invoice.amount_total,\n"
        "$amount_due=invoice.residual,\n"
        "$total_debit=total amount to pay",
    )
    mail_template = fields.Many2one(
        "mail.template",
        domain="[('model_id', '=', 'res.partner')]",
        help="Mail template to use. You have to use a Partner model template.",
    )
    code = fields.Char("Code", help="Code. Can be used in cron job to run only selected followups")

    @api.model
    def is_match(self, date):
        target_date = date + relativedelta(days=self.relative_days)
        today = fields.Date.context_today(self)
        if self.match == "=":
            if today == target_date:
                return True
            else:
                return False
        if self.match == ">=":
            if today >= target_date:
                return True
            else:
                return False

    @api.model
    def send_now(self):
        wizard = self.env["followup.send"].create([])
        wizard.run_followup()
