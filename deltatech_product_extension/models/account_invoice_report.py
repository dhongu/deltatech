# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    manufacturer = fields.Many2one("res.partner", string="Manufacturer", readonly=True)

    def _select_list(self, table):
        return super()._select_list(table) + [
            SQL("%s AS manufacturer", table.product_id.product_tmpl_id.manufacturer),
        ]
