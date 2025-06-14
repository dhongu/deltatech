# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ValuationArea(models.Model):
    _name = "valuation.area"
    _description = "Valuation Area"

    name = fields.Char(required=True)
    code = fields.Char(required=True, help="Short code used in account determination")
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    stock_journal_id = fields.Many2one("account.journal", string="Stock Journal")
