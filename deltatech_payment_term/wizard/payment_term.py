# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_round


class AccountPaymentTermRateWizard(models.TransientModel):
    _name = "account.payment.term.rate.wizard"
    _description = "Payment Term Rate Wizard"

    name = fields.Char(string="Name", required=True)
    rate = fields.Integer(string="Number of rates", required=True)
    advance = fields.Float(string="Advance", digits="Payment Term", required=True)
    rate_value = fields.Float(string="Rate Value")
    day_of_the_month = fields.Integer(string="Day of the Month", required=True)
    term_id = fields.Many2one("account.payment.term")
    value = fields.Selection(
        [("percent", "Percent"), ("fixed", "Fixed Amount")],
        string="Type",
        required=True,
        default="percent",
        help="Select here the kind of valuation related to this payment terms line.",
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super(AccountPaymentTermRateWizard, self).default_get(fields_list)
        active_model = self.env.context.get("active_model", False)
        active_id = self.env.context.get("active_id", False)
        if active_model == "account.payment.term":
            term = self.env[active_model].browse(active_id)
            defaults["term_id"] = active_id
            defaults["name"] = term.name
            if term.line_ids:
                defaults["rate"] = len(term.line_ids) - 1
        return defaults

    @api.constrains("rate")
    def _check_rate(self):
        if self.rate < 1:
            raise ValidationError(_("Rate must be greater than 1"))

    @api.constrains("advance")
    def _check_advance(self):
        if self.value == "percent" and (self.advance < 0.0 or self.advance > 100.0):
            raise ValidationError(_("Percentages for Advance must be between 0 and 100."))

    def do_create_rate(self):
        line_ids = []

        if self.value == "percent":

            first_rate = {
                "value": "percent",
                "value_amount": self.advance,
                "days": 0,
                "day_of_the_month": self.day_of_the_month,
                "option": "day_after_invoice_date",
            }
            line_ids.append((0, 0, first_rate))

            if self.rate > 1:
                rest = 100 * (1 - self.advance / 100) / (self.rate)

            for x in range(1, self.rate + 1):
                norm_rate = {
                    "value": "percent",
                    "value_amount": float_round(rest, 6, rounding_method="DOWN"),
                    "days": 30 * x,
                    "day_of_the_month": self.day_of_the_month,
                    "option": "day_after_invoice_date",
                }
                line_ids.append((0, 0, norm_rate))
        else:

            first_rate = {
                "value": "fixed",
                "value_amount": self.advance,
                "days": 0,
                "day_of_the_month": self.day_of_the_month,
                "option": "day_after_invoice_date",
            }
            line_ids.append((0, 0, first_rate))

            for x in range(1, self.rate + 1):
                norm_rate = {
                    "value": "fixed",
                    "value_amount": self.rate_value,
                    "days": 30 * x,
                    "day_of_the_month": self.day_of_the_month,
                    "option": "day_after_invoice_date",
                }
                line_ids.append((0, 0, norm_rate))

        line_ids[-1] = (
            0,
            0,
            {
                "value": "balance",
                "days": 30 * (self.rate),
                "day_of_the_month": self.day_of_the_month,
                "option": "day_after_invoice_date",
            },
        )

        if not self.term_id:
            self.env["account.payment.term"].create({"name": self.name, "line_ids": line_ids})
        else:
            self.term_id.line_ids.unlink()
            self.term_id.write({"name": self.name, "line_ids": line_ids})
