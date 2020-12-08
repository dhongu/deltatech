# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_ready = fields.Boolean(string="Is ready", compute="_compute_is_ready")

    stage = fields.Selection(
        [
            ("placed", "Placed"),  # comanda plasta pe website
            ("in_process", "In Process"),  # comanda in procesare de catre agentul de vanzare
            ("waiting", "Waiting availability"),  # nu sunt in stoc toate produsele din comanda
            ("to_be_delivery", "To Be Delivery"),  # comanda este de livrat
            ("in_delivery", "In Delivery"),  # marfa a fost predata la curier
            ("delivered", "Delivered"),  # comanda a fost livrata la client
            ("canceled", "Canceled"),
            ("returned", "Returned"),
        ],
        default="placed",
        string="Stage",
        copy=False,
        index=True,
        tracking=True,
        compute="_compute_stage",
        store=True,
    )

    payment_status = fields.Selection(
        [("without", "Without"), ("initiated", "Initiated"), ("authorized", "Authorized"), ("done", "Done")],
        default="without",
        compute="_compute_payment_status",
        store=True,
    )

    @api.depends("state", "website_id", "picking_ids.state", "picking_ids.delivery_state")
    def _compute_stage(self):
        for order in self:
            order.stage = "in_process"

            if order.state == "sent" and order.website_id:
                order.stage = "placed"
            if order.state == "draft" and order.website_id:
                order.stage = False
            elif order.state == "cancel":
                order.stage = "canceled"
            else:
                order.stage = "in_process"

            if order.stage == "in_process" and order.state == "sale":
                qty_to_deliver = 0
                order.stage = "delivered"
                for line in order.order_line:
                    qty_to_deliver += line.qty_to_deliver
                if qty_to_deliver != 0:
                    order.stage = "to_be_delivery"
                else:
                    for picking in order.picking_ids:
                        if picking.delivery_state not in ["draft", "delivered"]:
                            order.stage = "in_delivery"

                for picking in order.picking_ids:
                    if picking.state in ["waiting", "confirmed"]:
                        order.stage = "waiting"

    @api.depends("transaction_ids", "invoice_ids")
    def _compute_payment_status(self):
        for order in self:
            order.payment_status = "without"
            if order.transaction_ids:
                order.payment_status = "initiated"
                authorized_transaction_ids = order.transaction_ids.filtered(lambda t: t.state == "authorized")
                if authorized_transaction_ids:
                    order.payment_status = "authorized"
                done_transaction_ids = order.transaction_ids.filtered(lambda t: t.state == "done")
                if done_transaction_ids:
                    order.payment_status = "done"
            if order.payment_status != "done" and order.invoice_ids:
                paid = True
                for invoice in order.invoice_ids:
                    if invoice.invoice_payment_state != "paid":
                        paid = False
                        break
                if paid:
                    order.payment_status = "done"

    def _compute_is_ready(self):
        for order in self:

            is_ready = order.state in ["draft", "sent", "sale", "done"] and order.invoice_status != "invoiced"
            if is_ready:
                for line in order.order_line:
                    is_ready = is_ready and (line.qty_available_today >= line.product_uom_qty)
            order.is_ready = is_ready
