# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    stage = fields.Selection(
        [
            ("placed", "Placed"),  # comanda plasta pe website
            ("in_process", "In Process"),  # comanda in procesare de catre agentul de vanzare
            ("waiting", "Waiting availability"),  # nu sunt in stoc toate produsele din comanda
            ("postponed", "Postponed"),  # livrarea a fost amanata
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

    @api.depends("state", "website_id", "picking_ids.state", "picking_ids.delivery_state", "postponed_delivery")
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

            if order.stage == "in_process" and order.postponed_delivery:
                order.stage = "postponed"

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
