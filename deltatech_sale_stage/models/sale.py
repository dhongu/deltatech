# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    stage_id = fields.Many2one("sale.order.stage", string="Stage", copy=False, tracking=True)
    stage_ids = fields.Many2many(
        "sale.order.stage",
        string="Stages",
        readonly=False,
        compute="_compute_stage_ids",
        inverse="_inverse_stage_ids",
    )

    @api.depends("stage_id")
    def _compute_stage_ids(self):
        for order in self:
            order.stage_ids = order.stage_id

    def _inverse_stage_ids(self):
        for order in self:
            order.stage_id = order.stage_ids[0] if order.stage_ids else False

    def _get_invoice_status(self):
        res = super()._get_invoice_status()
        orders_invoiced = self.filtered(lambda o: o.invoice_status == "invoiced")
        orders_invoiced.set_stage("invoiced")
        return res

    @api.onchange("stage_id")
    def onchange_stage_id(self):
        if self.stage_id.invoiced and self.invoice_status == "invoiced":
            raise UserError(_("The order was not invoiced"))

    def action_confirm(self):
        res = super().action_confirm()
        self.set_stage("confirmed")
        return res

    def action_quotation_sent(self):
        res = super().action_quotation_sent()
        self.set_stage("send_email")
        return res

    def action_cancel(self):
        res = super().action_cancel()
        self.set_stage("canceled")
        return res

    def set_stage(self, stage_step):
        domain = [(stage_step, "=", True)]
        stages = self.env["sale.order.stage"].search(domain)
        if not stages:
            return
        for order in self:
            transactions = order.sudo().transaction_ids.filtered(lambda a: a.state == "done")
            relevant_stage = stages
            if transactions:
                relevant_stage = stages.filtered(lambda s: s.paid)
            if not relevant_stage:
                relevant_stage = stages

            new_stage = relevant_stage[0]
            for stage in relevant_stage:
                if stage.sequence > order.stage_id.sequence:
                    new_stage = stage
                    break
            order.stage_id = new_stage

    def write(self, vals):
        res = super().write(vals)
        if "stage_id" in vals:
            if self.stage_id.action_id:
                self.stage_id.action_id.run()
        return res
