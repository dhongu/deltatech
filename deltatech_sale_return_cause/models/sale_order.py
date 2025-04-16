from datetime import datetime, timedelta

from odoo import api, fields, models


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
        ],
        string="Return Cause",
    )
    return_amount = fields.Float(string="Return Amount", digits="Product Price", default=0.0, readonly=True)

    @api.model
    def _cron_check_and_update_return_amount(self):
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
