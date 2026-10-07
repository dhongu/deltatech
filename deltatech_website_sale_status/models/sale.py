# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from datetime import timedelta

from odoo import api, fields, models

# Parameter of the detailed stage: the website quotation sent to the customer
# is `placed` and the stage follows the carrier status of the transfers.
DETAILED_STAGE_PARAM = "deltatech_website_sale_status.detailed_stage"
# The carrier status is tracked for the transfers validated in the last days
# (`_cron_get_status_history`). An older transfer keeps the last status read,
# which is not the final one when the carrier stopped answering.
CARRIER_TRACKING_DAYS = 30


class SaleOrder(models.Model):
    _inherit = "sale.order"

    stage = fields.Selection(
        [
            ("placed", "Placed"),  # comanda plasta pe website
            ("in_process", "In Process"),  # comanda in procesare de catre agentul de vanzare
            ("rfq", "Request for Quotation"),  # oferta trimisa furnizorului
            ("waiting", "Waiting availability"),  # nu sunt in stoc toate produsele din comanda
            ("postponed", "Postponed"),  # livrarea a fost amanata
            ("to_be_delivery", "To Be Delivery"),  # comanda este de livrat
            ("pre_advice", "Pre advice"),  # awb generat
            ("in_delivery", "In Delivery"),  # marfa a fost predata la curier Expediata
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

    @api.depends(
        "state",
        "website_id",
        "picking_ids.state",
        "picking_ids.delivery_state",
        "postponed_delivery",
    )
    def _compute_stage(self):
        detailed = self._is_detailed_stage()
        for order in self:
            order.stage = "in_process"

            if detailed and order.state == "sent" and order.website_id:
                order.stage = "placed"
            elif order.state == "draft" and order.website_id:
                order.stage = False
            elif order.state == "cancel":
                order.stage = "canceled"

            if order.stage == "in_process" and order.postponed_delivery:
                order.stage = "postponed"

            if order.stage == "in_process" and order.state in ["sale", "done"]:
                qty_to_deliver = 0

                for line in order.order_line:
                    if line.product_id.is_storable:
                        qty_to_deliver += line.qty_to_deliver
                if qty_to_deliver != 0:
                    order.stage = "to_be_delivery"
                else:
                    order.stage = "delivered"
                    final_states = ["draft", "delivered", "pre_advice"] if detailed else ["draft", "delivered"]
                    for picking in order.picking_ids:
                        if picking.delivery_state not in final_states:
                            order.stage = "in_delivery"

                for picking in order.picking_ids:
                    if picking.state in ["waiting", "confirmed"]:
                        order.stage = "waiting"

                if order.stage == "to_be_delivery" and not order.picking_ids:
                    order.stage = "waiting"
                    # purchase_order_count and _get_purchase_orders() come from
                    # sale_purchase, which is not a dependency: without it there
                    # is no RFQ to look at.
                    if "purchase_order_count" in order._fields and order.sudo().purchase_order_count > 0:
                        purchase_orders = order._get_purchase_orders()
                        for purchase_order in purchase_orders:
                            if purchase_order.state == "sent":
                                order.stage = "rfq"

                # if all pickings are delivered, sale order must be delivered
                # without backorder, not all quantities are delivered but all pickings are done
                if order.picking_ids:
                    if len(order.picking_ids.mapped("state")) == 1 and order.picking_ids.mapped("state")[0] == "done":
                        order.stage = "delivered"

                    # if all pickings are delivered or canceled, sale order must be delivered
                    all_delivered = True
                    for picking in order.picking_ids:
                        if picking.state not in ["done", "cancel"]:
                            all_delivered = False
                    if all_delivered:
                        order.stage = "delivered"

                if detailed and order.stage in ["to_be_delivery", "delivered"]:
                    order.stage = order._get_stage_from_delivery_state() or order.stage

    @api.model
    def _is_detailed_stage(self):
        """The detailed stage is enabled in the Sales settings (off by default).

        Off, the order is `delivered` at the validation of its transfers. On,
        the website quotation sent to the customer is `placed` and the stage
        follows the carrier status of the transfers.
        """
        return bool(self.env["ir.config_parameter"].sudo().get_param(DETAILED_STAGE_PARAM))

    def _get_stage_from_delivery_state(self):
        """Stage given by the carrier status (`delivery_state`) of the transfers.

        Applied over a stock stage of `to_be_delivery`/`delivered`: the goods
        are ready or the transfers are validated, but what the customer sees
        follows the parcel. An AWB generated (`pre_advice`), a parcel with the
        carrier (`in_transit`/`in_warehouse`/`in_delivery`) or delivered to
        all its recipients (`delivered`). Returns False when the carrier gave
        no such status, and the stock stage stays.

        Only the transfers still tracked count: a transfer validated more than
        `CARRIER_TRACKING_DAYS` ago keeps the last status read, not the final
        one, and the order keeps its stock stage.
        """
        self.ensure_one()
        tracked_since = fields.Datetime.now() - timedelta(days=CARRIER_TRACKING_DAYS)
        pickings = self.picking_ids.filtered(
            lambda p: p.state != "cancel" and (not p.date_done or p.date_done >= tracked_since)
        )
        delivery_states = set(pickings.mapped("delivery_state"))
        if delivery_states & {"in_transit", "in_warehouse", "in_delivery"}:
            return "in_delivery"
        if "pre_advice" in delivery_states:
            return "pre_advice"
        if delivery_states == {"delivered"}:
            return "delivered"
        return False

    def _action_confirm(self):
        res = super()._action_confirm()
        self._compute_stage()
        return res
