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
                # if order is confirmed and there are no pickings, it should be a services order and it should be done
                if order.state in ["purchase", "done"]:
                    order.picking_status = "done"
                else:
                    order.picking_status = "in_progress"
            else:
                state = "done"
                for picking in order.picking_ids:
                    if picking.state not in ["done", "cancel"]:
                        state = "in_progress"
                order.picking_status = state

    def _search_picking_status(self, operator, value):
        # În Odoo 19 ORM-ul normalizează `("picking_status", "=", "x")` la
        # operatorul `in` cu o colecție de valori, deci trebuie tratate atât
        # `in`/`not in` (value = listă/set) cât și `=`/`!=` (value = scalar).
        if operator in ("in", "not in"):
            values = set(value)
        elif operator in ("=", "!="):
            values = {value}
        else:
            raise NotImplementedError(self.env._("Operator %s not supported", operator))
        orders = self.search([("state", "!=", "cancel")])
        f_orders = orders.filtered(lambda x: x.picking_status in values)
        if operator in ("not in", "!="):
            f_orders = orders - f_orders
        return [("id", "in", f_orders.ids)]
