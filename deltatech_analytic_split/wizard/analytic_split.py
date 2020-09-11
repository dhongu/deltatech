# ©  2008-2020 Terrabit
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models
from odoo.exceptions import Warning


class AnalyticLineSplit(models.TransientModel):
    _name = "analytic.line.split"
    _description = "Analytic line split"

    from_analytic_line = fields.Many2one("account.analytic.line", string="From line")
    from_analytic = fields.Many2one(
        "account.analytic.account", related="from_analytic_line.account_id", string="From", readonly=True
    )
    to_analytics = fields.One2many("analytic.line.split.lines", "analytic_split_id", string="To accounts")
    currency_id = fields.Many2one("res.currency", related="from_analytic_line.currency_id")
    from_amount = fields.Monetary(string="From amount", currency_field="currency_id", readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super(AnalyticLineSplit, self).default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        if active_id:
            res["from_analytic_line"] = active_id
            analytic_line = self.env["account.analytic.line"].browse(active_id)
            res["from_amount"] = analytic_line.amount
        else:
            raise Warning(_("Please select a record"))
        return res

    @api.multi
    def do_transfer(self):
        self.ensure_one()

        # test amounts
        line_amount = 0.0
        for line in self.to_analytics:
            line_amount += line.amount
            # check signs
            if abs(self.from_amount + line.amount) != abs(self.from_amount) + abs(line.amount):
                raise Warning(_("Amount error: different signs"))
        # check value
        if abs(line_amount) > abs(self.from_amount):
            raise Warning(_("Amount error: amounts exceeds original line amount"))

        note = _("Split from line amount %s:<br/>" % self.from_amount)
        for line in self.to_analytics:
            newline = self.from_analytic_line.copy()
            newline.update({"amount": line.amount, "account_id": line.analytic_account.id})
            reverse_analytic = newline.copy()
            reverse_analytic.update({"amount": -line.amount, "account_id": self.from_analytic_line.account_id})
            # add to note
            note += _("%s: %s<br/>" % (line.description, line.amount))

        # post notes
        self.from_analytic_line.message_post(body=note)

        return True


class AnalyticLineSplitLines(models.TransientModel):
    _name = "analytic.line.split.lines"
    _description = "Analytic line split lines"

    analytic_split_id = fields.Many2one("analytic.line.split")
    description = fields.Char(required=True)
    analytic_account = fields.Many2one("account.analytic.account", required=True)
    date = fields.Date("Date", default=fields.Date.today)
    currency_id = fields.Many2one("res.currency", related="analytic_split_id.currency_id")
    amount = fields.Monetary(default=0.0, currency_field="currency_id", required=True)


# inherit mail for messages
class AccountAnalyticLine(models.Model):
    _name = "account.analytic.line"
    _inherit = ["account.analytic.line", "mail.thread"]

    amount = fields.Monetary("Amount", required=True, default=0.0, track_visibility="always")
