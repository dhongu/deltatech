from odoo import api, fields, models


class AccountInvoiceChangeNumber(models.TransientModel):
    _name = "account.invoice.change.number"
    _description = "Account Invoice Change Number"

    internal_number = fields.Char(string="Invoice Number", required=True)

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id")
        if active_id and "internal_number" in fields_list:
            defaults["internal_number"] = self.env["account.move"].browse(active_id).name
        return defaults

    def do_change_number(self):
        self.ensure_one()
        active_id = self.env.context.get("active_id")
        if active_id:
            invoice = self.env["account.move"].browse(active_id).exists()
            invoice.write({"name": self.internal_number})
            invoice.action_number()
        return {"type": "ir.actions.act_window_close"}
