# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    manufacturer = fields.Many2one("res.partner", string="Manufacturer", readonly=True)

    @api.model
    def _select(self) -> SQL:
        select_str = super()._select().code + ", template.manufacturer"
        return SQL(select_str)

    # def _group_by(self):
    #     group_by_str = super()._group_by() + ", template.manufacturer"
    #     return group_by_str
