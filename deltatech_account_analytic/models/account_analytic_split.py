# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class AccountAnalyticSplitTemplate(models.Model):
    _name = "account.analytic.split.template"
    _description = "Analytic split template"
    _order = "sequence, id"

    name = fields.Char(string="Name")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean()
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
    state = fields.Selection([("draft", "Draft"), ("confirmed", "Confirmed")])
    line_to_split = fields.Many2one("account.analytic.line")
    line_ids = fields.One2many("account.analytic.split.line", "split_id", string="Split lines")


class AccountAnalyticSplitLine(models.Model):
    _name = "account.analytic.split.line"
    _description = "Analytic split line"
    _order = "sequence, id"

    split_id = fields.Many2one("account.analytic.split")
    sequence = fields.Integer(string="Sequence", default=10)
    analytic_id = fields.Many2one("account.analytic.account")
    percent = fields.Integer(string="Percent %")
    amount = fields.Float("Amount")
    analytic_line_id = fields.Many2one("account.analytic.line")
