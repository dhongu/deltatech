# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


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

    def action_cancel(self):
        res = super().action_cancel()
        self.set_phase("canceled")
        return res

    def set_phase(self, phase_step):
        domain = [(phase_step, "=", True)]
        phases = self.env["sale.order.phase"].search(domain)
        if not phases:
            return
        for order in self:
            transactions = order.sudo().transaction_ids.filtered(lambda a: a.state == "done")
            relevant_phase = phases
            if transactions:
                relevant_phase = phases.filtered(lambda s: s.paid)
            if not relevant_phase:
                relevant_phase = phases

            new_phase = relevant_phase[0]
            for phase in relevant_phase:
                if phase.sequence > order.phase_id.sequence:
                    new_phase = phase
                    break
            order.phase_id = new_phase

    def write(self, vals):
        res = super().write(vals)
        if "phase_id" in vals:
            if self.phase_id.action_id:
                self.phase_id.action_id.run()
        return res
