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
        if self.env.context.get("skip_phase_update", False):
            return
        domain = [(phase_step, "=", True)]
        # sudo doar pentru citirea fazelor: utilizatorul (ex. contabilul) poate să nu aibă drepturi pe ele
        phases = self.env["sale.order.phase"].sudo().search(domain)
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
                if phase.sequence > order.phase_id.sudo().sequence:
                    new_phase = phase
                    break

            if new_phase and new_phase != order.phase_id:
                # sudo doar pentru scrierea fazei; efectele (acțiune, confirmare, anulare) rulează cu drepturile
                # utilizatorului, cheia din context e citită în write()
                if self.env.su:
                    order.phase_id = new_phase  # apelant deja sudo: efectele păstrează mediul lui
                else:
                    order.sudo().with_context(phase_actions_as_user=True).phase_id = new_phase

    def write(self, vals):
        res = super().write(vals)
        if "phase_id" in vals:
            for order in self:
                phase = order.phase_id.sudo()  # citire: ir.rule pe fază
                if self.env.context.get("phase_actions_as_user"):
                    # scrierea a fost ridicată cu sudo în set_phase: efectele rulează ca utilizatorul curent
                    order = order.with_user(self.env.user)
                if phase.action_id:
                    # acțiunea se rulează în mediul comenzii (al apelantului), nu în cel sudo al fazei
                    action = order.env["ir.actions.server"].browse(phase.action_id.id)
                    action.with_context(active_id=order.id, active_model="sale.order").run()
                if phase.confirmed and order.state == "draft":
                    order.with_context(skip_phase_update=True).action_confirm()
                if phase.canceled and order.state != "cancel":
                    order.with_context(skip_phase_update=True)._action_cancel()
        return res
