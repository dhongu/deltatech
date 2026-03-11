# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    stage_route_id = fields.Many2one("sale.order.stage.route", string="Stage Route")
    phase_id = fields.Many2one(
        "sale.order.phase",
        string="Phase",
        copy=False,
        tracking=True,
        group_expand="_read_group_phase_ids",
    )

    @api.model
    def _read_group_phase_ids(self, phases, domain):
        return self.env["sale.order.phase"].search([])

    @api.onchange("stage_route_id")
    def _onchange_stage_route_id(self):
        if self.stage_route_id and self.stage_route_id.line_ids:
            self.phase_id = self.stage_route_id.line_ids[0].phase_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("stage_route_id") and not vals.get("phase_id"):
                route = self.env["sale.order.stage.route"].browse(vals.get("stage_route_id"))
                if route.line_ids:
                    vals["phase_id"] = route.line_ids[0].phase_id.id
        return super().create(vals_list)

    def write(self, vals):
        if "stage_route_id" in vals and vals.get("stage_route_id") and "phase_id" not in vals:
            route = self.env["sale.order.stage.route"].browse(vals.get("stage_route_id"))
            if route.line_ids:
                vals["phase_id"] = route.line_ids[0].phase_id.id
        return super().write(vals)
