# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    phase_id = fields.Many2one("sale.order.phase", string="Phase", copy=False, tracking=True)
    phase_ids = fields.Many2many(
        "sale.order.phase",
        string="Phases",
        readonly=False,
        compute="_compute_phase_ids",
        inverse="_inverse_phase_ids",
    )

    @api.depends("phase_id")
    def _compute_phase_ids(self):
        for order in self:
            order.phase_ids = order.phase_id

    def _inverse_phase_ids(self):
        for order in self:
            order.phase_id = order.phase_ids[0] if order.phase_ids else False

    def _get_invoice_status(self):
        res = super()._get_invoice_status()
        orders_invoiced = self.filtered(lambda o: o.invoice_status == "invoiced")
        orders_invoiced.set_phase("invoiced")
        return res

    @api.onchange("phase_id")
    def onchange_phase_id(self):
        if self.phase_id.invoiced and self.invoice_status == "invoiced":
            raise UserError(_("The order was not invoiced"))

    def action_confirm(self):
        res = super().action_confirm()
        self.set_phase("confirmed")
        return res

    def action_quotation_sent(self):
        res = super().action_quotation_sent()
        self.set_phase("send_email")
        return res

    def _action_cancel(self):
        res = super()._action_cancel()
        self.set_phase("canceled")
        return res

    def set_phase(self, phase_step, ignore_sequence=False):
        if self.env.context.get("skip_phase_update", False):
            return
        if phase_step not in self.env["sale.order.phase"]._fields:
            domain = [("code", "=", phase_step)]
        else:
            domain = [(phase_step, "=", True)]
        phases = self.env["sale.order.phase"].search(domain)

        if not phases:
            return
        for order in self:
            transactions = order.sudo().transaction_ids.filtered(lambda a: a.state == "done")
            relevant_phase = False
            if transactions:
                relevant_phase = phases.filtered(lambda s: s.paid)
            if not relevant_phase:
                relevant_phase = phases

            new_phase = False
            for phase in relevant_phase:
                if ignore_sequence:
                    new_phase = phase
                    break
                if phase.sequence > order.phase_id.sequence:
                    new_phase = phase
                    break

            if new_phase and new_phase != order.phase_id:
                order.phase_id = new_phase

    def write(self, vals):
        res = super().write(vals)
        if "phase_id" in vals:
            for order in self:
                order = order.with_context(active_id=order.id, active_model="sale.order")
                if order.phase_id.action_id:
                    try:
                        order.phase_id.action_id.run()
                    except Exception as e:
                        _logger.error(e)
                if order.phase_id.confirmed and order.state == "draft":
                    order.with_context(skip_phase_update=True).action_confirm()
                if order.phase_id.canceled and order.state != "cancel":
                    order.with_context(skip_phase_update=True)._action_cancel()
        return res
