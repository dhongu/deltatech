# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    phase_id = fields.Many2one("sale.order.phase", string="Phase", copy=False, tracking=True)

    @api.onchange("phase_id")
    def onchange_phase_id(self):
        if self.phase_id.invoiced and self.invoice_status == "invoiced":
            raise UserError(self.env._("The order was not invoiced"))

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
        if not self or self.env.context.get("skip_phase_update", False):
            return
        domain = [(phase_step, "=", True)]
        # the phases are configuration: a user without sales rights (e.g. an accountant posting the invoice)
        # must still be able to move the order to the next phase
        phases = self.env["sale.order.phase"].sudo().search(domain)
        if not phases:
            return
        for order in self:
            current_phase = order.sudo().phase_id
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
                if phase.sequence > current_phase.sequence:
                    new_phase = phase
                    break

            if new_phase and new_phase != current_phase:
                order.phase_id = new_phase

    def write(self, vals):
        res = super().write(vals)
        if "phase_id" in vals:
            for order in self:
                if order.phase_id.action_id:
                    order.phase_id.action_id.with_context(active_id=order.id, active_model="sale.order").run()
                if order.phase_id.confirmed and order.state == "draft":
                    order.with_context(skip_phase_update=True).action_confirm()
                if order.phase_id.canceled and order.state != "cancel":
                    order.with_context(skip_phase_update=True)._action_cancel()
        return res
