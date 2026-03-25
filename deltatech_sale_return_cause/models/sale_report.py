from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    return_cause_id = fields.Many2one("sale.return.cause", string="Return Cause", readonly=True)
    return_cause = fields.Selection(
        selection=[
            ("not_satisfied", "Not satisfied with quality"),
            ("wrong_shipped", "Wrongly shipped warehouse"),
            ("ordered_incorrectly", "Ordered incorrectly by client"),
            ("does_not_fit", "Does not fit"),
            ("sale_team_mistake", "Incorrectly advised by Sales"),
            ("duplicate_order", "Duplicate order"),
            ("does_not_expect", "Does not expect the order"),
            ("200_warranty", "200% warranty"),
            ("not_picked", "Package not picked up by client"),
            ("b2b_return", "B2B Return"),
            ("exchange", "Exchange"),
            ("external_tva_restitution", "External TVA Restitution"),
            ("lost_package", "Lost Package"),
        ],
        string="Return Cause(Legacy)",
        readonly=True,
    )
    return_cause_date = fields.Date(string="Return Cause Date", readonly=True)

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res["return_cause_id"] = "s.return_cause_id"
        res["return_cause"] = "s.return_cause"
        res["return_cause_date"] = "s.return_cause_date"
        return res

    def _group_by_sale(self):
        res = super()._group_by_sale()
        res += ", s.return_cause_id, s.return_cause, s.return_cause_date"
        return res
