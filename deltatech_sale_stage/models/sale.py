# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    stage_id = fields.Many2one("sale.order.stage", string="Stage", copy=False)
    stage_ids = fields.Many2many("sale.order.stage", string="Stage", compute="_compute_stage_ids")

    def _compute_stage_ids(self):
        for order in self:
            order.stage_ids = order.stage_id

    def _get_invoice_status(self):
        super(SaleOrder, self)._get_invoice_status()
        orders_invoiced = self.filtered(lambda o: o.invoice_status == "invoiced")
        orders_invoiced.set_stage("invoiced")

    @api.onchange("stage_id")
    def onchange_stage_id(self):
        if self.stage_id.invoiced and self.invoice_status == "invoiced":
            raise UserError(_("The order was not invoiced"))

    def action_confirm(self):
        super(SaleOrder, self).action_confirm()
        self.set_stage("confirmed")

    def action_quotation_sent(self):
        super(SaleOrder, self).action_quotation_sent()
        self.set_stage("send_email")

    def set_stage(self, stage_step):
        domain = [(stage_step, "=", True)]
        stage = self.env["sale.order.stage"].search(domain, limit=1)
        for order in self:
            if not order.stage_id or not order.stage_id[stage_step]:
                order.stage_id = stage

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if "stage_id" in vals:
            if self.stage_id.action_id:
                self.stage_id.action_id.run()
        return res
