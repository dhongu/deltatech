# ©  2023-now Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    category_type = fields.Many2one("category.group.type", readonly=True)
    category_class = fields.Many2one("category.group.class", readonly=True)

    @api.model
    def _select(self) -> SQL:
        select_str = super()._select().code
        select_str += """
            , categ.category_group_type as category_type, categ.category_group_class as category_class
        """
        return SQL(select_str)

    def _from(self) -> SQL:
        return SQL("%s left join product_category categ on template.categ_id = categ.id", super()._from())
