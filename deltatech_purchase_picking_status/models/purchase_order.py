# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.fields import Domain


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

    @api.depends("state", "picking_ids", "picking_ids.state")
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
        # Domeniul reproduce exact regula din _compute_picking_status, fără
        # filtru pe starea comenzii (și comenzile anulate au un status afișat).
        in_progress = Domain.OR(
            [
                Domain("picking_ids", "=", False) & Domain("state", "not in", ["purchase", "done"]),
                Domain("picking_ids", "any", [("state", "not in", ["done", "cancel"])]),
            ]
        )
        domains = []
        if "in_progress" in values:
            domains.append(in_progress)
        if "done" in values:
            domains.append(~in_progress)
        domain = Domain.OR(domains) if domains else Domain.FALSE
        if operator in ("not in", "!="):
            domain = ~domain
        return domain
