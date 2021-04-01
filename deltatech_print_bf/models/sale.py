# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def default_get(self, fields):
        defaults = super(SaleOrder, self).default_get(fields)
        is_bf = self.env.context.get("is_bf", False)
        if is_bf:
            defaults["partner_id"] = self.env.ref("deltatech_partner_generic.partner_generic").id
        return defaults

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        is_bf = self.env.context.get("is_bf", False)
        partner_generic = self.env.ref("deltatech_partner_generic.partner_generic")
        if is_bf or self.partner_id == partner_generic:
            invoice_vals["move_type"] = "out_receipt"
        return invoice_vals

    @api.depends("order_line.invoice_lines")
    def _get_invoiced(self):
        super(SaleOrder, self)._get_invoiced()
        partner_generic = self.env.ref("deltatech_partner_generic.partner_generic")
        for order in self:
            if order.partner_id == partner_generic:
                invoices = order.order_line.invoice_lines.move_id.filtered(
                    lambda r: r.move_type in ("out_invoice", "out_receipt")
                )
                order.invoice_ids |= invoices
                order.invoice_count += len(invoices)

    def action_view_invoice(self):
        action = super(SaleOrder, self).action_view_invoice()
        partner_generic = self.env.ref("deltatech_partner_generic.partner_generic")
        if self.partner_id == partner_generic:
            action["context"] = {"default_move_type": "out_receipt"}
        return action


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("invoice_lines.move_id.state", "invoice_lines.quantity", "untaxed_amount_to_invoice")
    def _get_invoice_qty(self):

        super(SaleOrderLine, self)._get_invoice_qty()

        for line in self:
            qty_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.move_id.state != "cancel":
                    if invoice_line.move_id.type == "out_receipt":
                        qty_invoiced += invoice_line.product_uom_id._compute_quantity(
                            invoice_line.quantity, line.product_uom
                        )

            line.qty_invoiced += qty_invoiced
