# ©  2024 Terrabit Solutions
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import _, api, exceptions, fields, models
from odoo.tools.safe_eval import safe_eval


class SaleOrder(models.Model):
    _inherit = "purchase.order"

    po_type = fields.Many2one("record.type", string="Order Type", tracking=True)
    show_po_type = fields.Boolean(compute="_compute_show_po_type", store=False)
    journal_id = fields.Many2one("account.journal", string="Journal", domain="[('type', '=', 'purchase')]")

    @api.onchange("po_type")
    def _onchange_po_type(self):
        for default_value in self.po_type.default_values_ids:
            self[default_value.field_name] = safe_eval(default_value.field_value)

    @api.depends("po_type")  # need a depends, or it won't trigger compute on new
    def _compute_show_po_type(self):
        purchase_types = self.env["record.type"].search([("model", "=", "purchase.order")])
        for record in self:
            if purchase_types:
                record.show_po_type = True
            else:
                record.show_po_type = False

    def button_confirm(self):
        for order in self:
            if (
                not self.env.user.has_group("deltatech_record_type.group_confirm_order_without_record_type")
                and order.show_po_type
            ):
                if not order.po_type:
                    raise exceptions.UserError(
                        _("You do not have the rights to confirm an order without specifying an Order Type.")
                    )
        return super().button_confirm()

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.journal_id:
            invoice_vals["journal_id"] = self.journal_id.id
        return invoice_vals
