from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    # Add the new field to the report
    partner_email = fields.Char(string="Partner Email")


    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res['partner_email'] = " partner.email"
        return res

    # def _select_sale(self):
    #     # Extend the original _select_sale method to include partner_email
    #     select_ = super()._select_sale()
    #     select_ += ", partner.email AS partner_email"
    #     return select_

    def _group_by_sale(self):
        # Extend the original _group_by_sale method to include partner_email
        group_by_ = super()._group_by_sale()
        group_by_ += ", partner.email"
        return group_by_
