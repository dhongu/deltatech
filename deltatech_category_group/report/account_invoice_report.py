# ©  2023-now Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    category_type = fields.Many2one("category.group.type", readonly=True)
    category_class = fields.Many2one("category.group.class", readonly=True)

    def _select(self):
        select_str = super()._select()
        select_str += """
            , categ.category_group_type as category_type, categ.category_group_class as category_class
        """
        return select_str

    def _from(self):
        from_str = super()._from()
        from_str += """
            left join product_category categ on template.categ_id=categ.id
        """
        return from_str
