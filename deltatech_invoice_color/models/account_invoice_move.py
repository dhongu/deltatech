from odoo import api, fields, models


class AccountMoveLine(models.Model):
    """Override AccountInvoice_line to add the link to the purchase order line it is related to"""

    _inherit = "account.move.line"

    color_trigger = fields.Boolean(string="Trigger", compute="_compute_color_trigger")

    @api.depends("purchase_line_id", "sale_line_ids")
    def _compute_color_trigger(self):
        for line in self:
            if line.purchase_line_id or line.sale_line_ids:
                line.color_trigger = True
            else:
                line.color_trigger = False
