from datetime import datetime, timedelta

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class SaleOrder(models.Model):
    _inherit = "sale.order"

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
            ("b2b_return", "B2B Return")
        ],
        string="Return Cause",
    )
    return_amount = fields.Float(string="Return Amount", digits="Product Price", default=0.0)
    is_return_amount_readonly = fields.Boolean(compute="_compute_is_return_amount_readonly")

    def _compute_is_return_amount_readonly(self):
        auto_calculate = safe_eval(
            self.env["ir.config_parameter"].sudo().get_param("deltatech_sale_return_cause.auto_calculate", "True")
        )
        for order in self:
            order.is_return_amount_readonly = auto_calculate

    @api.model
    def _cron_check_and_update_return_amount(self):
        config_parameter = self.env["ir.config_parameter"].sudo()
        auto_calculate = safe_eval(config_parameter.get_param("deltatech_sale_return_cause.auto_calculate", "True"))
        if not auto_calculate:
            return
        one_year_ago = datetime.today() - timedelta(days=365)
        sale_orders = self.search([("date_order", ">=", one_year_ago), ("return_cause", "!=", False)])
        for order in sale_orders:
            order.check_and_update_return_amount()

    def check_and_update_return_amount(self):
        for order in self:
            if self.return_cause and self.invoice_count >= 2:
                # Get all credit notes related to these invoices
                credit_notes = self.invoice_ids.filtered(lambda x: x.move_type == "out_refund" and x.state == "posted")
                total_credit_amount = sum(credit_notes.mapped(lambda x: x.amount_total_signed))

                # Update the return_amount field
                order.return_amount = total_credit_amount
