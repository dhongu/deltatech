# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    picking_status = fields.Selection(
        [
            ("done", "Done"),  # order done
            ("in_progress", "In Progress"),  # order in progress
        ],
        default="in_progress",
        string="Delivery Status",
        copy=False,
        tracking=True,
        compute="_compute_picking_status",
        search="_search_picking_status",
    )

    def _compute_picking_status(self):
        for order in self:
            if not order.picking_ids:
                order.picking_status = "in_progress"
            else:
                state = "done"
                for picking in order.picking_ids:
                    if picking.state not in ["done", "cancel"]:
                        state = "in_progress"
                order.picking_status = state

    def _search_picking_status(self, operator, value):
        orders = self.search([("state", "!=", "cancel")])
        f_orders = orders.filtered(lambda x: x.picking_status == value)
        res = [("id", "in", [x.id for x in f_orders] if f_orders else False)]
        return res
