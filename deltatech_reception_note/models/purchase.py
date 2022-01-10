# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    reception_type = fields.Selection(
        [("normal", "Normal"), ("rfq_only", "RFQ Only"), ("note", "Reception Note")], string="Type", default="normal"
    )

    def action_rfq_send(self):
        if self.reception_type != "note":
            return super(PurchaseOrder, self).action_rfq_send()

    def set_sent(self):
        self.ensure_one()
        self.write({"state": "sent"})

    def button_confirm(self):
        orders = self
        for order in self:
            if order.reception_type == "rfq_only":
                orders -= order
        if not orders:
            raise UserError(_("Unable to confirm"))

        res = super(PurchaseOrder, orders).button_confirm()

        for order in self:
            if order.reception_type == "note":
                order.reduce_from_rfq()

        return res

    def reduce_from_rfq(self):
        domain = [("partner_id", "=", self.partner_id.id), ("reception_type", "=", "rfq_only"), ("state", "=", "sent")]
        rfq_orders = self.env["purchase.order"].search(domain)
        for line in self.order_line:
            quality = line.product_qty
            domain = [("order_id", "in", rfq_orders.ids), ("product_id", "=", line.product_id.id)]
            rfq_lines = self.env["purchase.order.line"].search(domain)
            if not rfq_lines:
                raise UserError(
                    _("The %s product (%s) is not found in a rfq")
                    % (line.product_id.name, line.product_id.default_code)
                )
            for rfq_line in rfq_lines:
                if quality < rfq_line.product_qty:
                    product_qty = rfq_line.product_qty - quality
                    rfq_line.write({"product_qty": product_qty})
                    quality = 0
                else:
                    quality -= rfq_line.product_qty
                    rfq_line.write({"product_qty": 0})
            if quality != 0:
                raise UserError(
                    _("The quantity of %s of the [%s] %s product is not found in a rfq")
                    % (
                        quality,
                        line.product_id.default_code,
                        line.product_id.name,
                    )
                )
