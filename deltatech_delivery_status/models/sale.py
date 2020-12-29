# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    postponed_delivery = fields.Boolean(string="Postponed delivery", compute="_compute_postponed_delivery")

    def postpone_delivery(self):
        pickings = self.env["stock.picking"]
        for order in self:
            pickings |= order.picking_ids.filtered(lambda p: p.state not in ["done", "cancel"])

        pickings.write({"postponed": True})

    def release_delivery(self):
        pickings = self.env["stock.picking"]
        for order in self:
            pickings |= order.picking_ids
        pickings.write({"postponed": False})

    def _compute_postponed_delivery(self):
        for order in self:
            order.postponed_delivery = any([p.postponed for p in order.picking_ids])
