# ©  2023-now Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import fields, models
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    category_type = fields.Many2one("category.group.type", readonly=True)
    category_class = fields.Many2one("category.group.class", readonly=True)

    def _select_list(self, table):
        return super()._select_list(table) + [
            SQL("%s AS category_type", table.product_id.categ_id.category_group_type),
            SQL("%s AS category_class", table.product_id.categ_id.category_group_class),
        ]
