# ©  2008-now Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

from odoo import fields, models


class SaleMarginReport(models.Model):
    _inherit = "sale.margin.report"

    category_type = fields.Many2one("category.group.type", string="Category type")
    category_class = fields.Many2one("category.group.class", string="Category class")

    def _select(self):
        select_str = super()._select()
        select_str += """
            , category_group_type as category_type, category_group_class as category_class
        """
        return select_str

    def _sub_select(self):
        select_str = super()._sub_select()
        select_str += """
            , c.category_group_type, c.category_group_class
        """
        return select_str

    def _from(self):
        from_str = super()._from()
        from_str += """
            left join product_category c on t.categ_id=c.id
        """
        return from_str

    def _group_by(self):
        group_by_str = super()._group_by()
        group_by_str += """
            , c.category_group_type, c.category_group_class
        """
        return group_by_str
