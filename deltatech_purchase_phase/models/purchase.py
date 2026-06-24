# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    phase_id = fields.Many2one("purchase.order.phase", string="Phase", copy=False, tracking=True)

    def set_phase(self, phase_step, ignore_sequence=False):
        if self.env.context.get("skip_phase_update", False):
            return
        domain = [("code", "=", phase_step)]
        phase = self.env["purchase.order.phase"].search(domain, limit=1)
        if not phase:
            phase = self.env["purchase.order.phase"].create({"code": phase_step, "name": phase_step})
        self.write({"phase_id": phase.id})

    def write(self, vals):
        res = super().write(vals)
        if "state" in vals:
            if vals["state"] == "sent":
                self.set_phase("rfq")
            if vals["state"] == "purchase":
                self.set_phase("purchase_confirm")
        return res
