# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    manufacturer = fields.Many2one("res.partner", string="Manufacturer", readonly=True)

    def _select(self):
        select_str = super(AccountInvoiceReport, self)._select() + ", template.manufacturer"
        return select_str

    def _group_by(self):
        group_by_str = super(AccountInvoiceReport, self)._group_by() + ", template.manufacturer"
        return group_by_str
