from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_type = fields.Many2one("record.type", string="Invoice Type", tracking=True)
    show_invoice_type = fields.Boolean(compute="_compute_show_invoice_type", store=False)

    @api.onchange("invoice_type")
    def _onchange_invoice_type(self):
        for default_value in self.invoice_type.default_values_ids:
            self[default_value.field_name] = safe_eval(default_value.field_value)

    @api.depends("invoice_type")  # need a depends or it won't trigger the compute on new
    def _compute_show_invoice_type(self):
        invoice_types = self.env["record.type"].search([("model", "=", "account.move")])
        for record in self:
            if invoice_types:
                record.show_invoice_type = True
            else:
                record.show_invoice_type = False
