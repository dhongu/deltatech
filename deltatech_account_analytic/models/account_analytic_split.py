# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountAnalyticSplitTemplate(models.Model):
    _name = "account.analytic.split.template"
    _description = "Analytic split template"
    _order = "sequence, id"

    name = fields.Char(string="Name")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(default=True)
    line_ids = fields.One2many("account.analytic.split.template.line", "split_template_id", string="Split lines")


class AccountAnalyticSplitTemplateLine(models.Model):
    _name = "account.analytic.split.template.line"
    _description = "Analytic split template line"
    _order = "sequence, id"

    split_template_id = fields.Many2one("account.analytic.split.template", ondelete="cascade")
    sequence = fields.Integer(string="Sequence", default=10)
    analytic_id = fields.Many2one("account.analytic.account")
    percent = fields.Integer(string="Percent %")


class AccountAnalyticSplit(models.Model):
    _name = "account.analytic.split"
    _description = "Analytic split"
    _order = "date DESC, id"

    name = fields.Char(string="Name")
    date = fields.Date(default=fields.Date.context_today)
    split_template_id = fields.Many2one("account.analytic.split.template")
    split_type = fields.Selection([("line", "Line"), ("amount", "Amount")], default="amount")
    state = fields.Selection([("draft", "Draft"), ("confirmed", "Confirmed")], default="draft")
    amount = fields.Float("Amount")
    line_to_split = fields.Many2one("account.analytic.line")
    line_ids = fields.One2many("account.analytic.split.line", "split_id", string="Split lines")

    def action_prepare_lines(self):
        self.ensure_one()
        self.check_template()
        if self.line_ids:
            self.line_ids.unlink()
        line_values = []
        if self.split_type == "line":
            self.amount = self.line_to_split.amount
        if not self.amount:
            raise UserError(_("Amount must be non-zero"))
        for template_line in self.split_template_id.line_ids:
            value = {
                "split_id": self.id,
                "analytic_id": template_line.analytic_id.id,
                "amount": self.amount * template_line.percent / 100,
                "percent": template_line.percent,
            }
            line_values.append(value)
        lines = self.line_ids.create(line_values)
        return lines

    def check_template(self):
        if self.split_template_id:
            percent = 0.0
            for line in self.split_template_id.line_ids:
                percent += line.percent
            if percent != 100.00:
                raise UserError(_("Invalid template. Sum of percents must be 100"))
        else:
            raise UserError(_("You must select a split template"))

    def action_create_analytic_lines(self):
        self.ensure_one()
        analytic_lines = self.env["account.analytic.line"]
        for line in self.line_ids:
            value = {
                "name": self.name if self.split_type == "amount" else self.name + " | " + self.line_to_split.name,
                "account_id": line.analytic_id.id,
                "amount": line.amount,
                "date": self.date,
            }
            analytic_line = self.env["account.analytic.line"].create(value)
            analytic_lines += analytic_line
            line.write({"analytic_line_id": analytic_line.id})
        self.write({"state": "confirmed"})
        if self.split_type == "line":
            self.line_to_split.unlink()
        return analytic_lines

    def action_reset_split(self):
        self.ensure_one()
        if self.split_type == "line":
            raise UserError(_("This operation is not permitted for this type of split (Line)"))
        self.line_ids.analytic_line_id.unlink()
        self.write({"state": "draft"})


class AccountAnalyticSplitLine(models.Model):
    _name = "account.analytic.split.line"
    _description = "Analytic split line"
    _order = "id"

    split_id = fields.Many2one("account.analytic.split")
    analytic_id = fields.Many2one("account.analytic.account")
    percent = fields.Integer(string="Percent %")
    amount = fields.Float("Amount")
    analytic_line_id = fields.Many2one("account.analytic.line")
