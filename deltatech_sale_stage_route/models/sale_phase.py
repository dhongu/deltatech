# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderStageRoute(models.Model):
    _name = "sale.order.stage.route"
    _description = "Sale Order Stage Route"

    name = fields.Char(required=True)
    line_ids = fields.One2many("sale.order.stage.route.line", "route_id", string="Stages", copy=True)

    @api.constrains("line_ids")
    def _check_unique_stages(self):
        for route in self:
            stages = route.line_ids.mapped("phase_id")
            if len(stages) != len(set(stages)):
                raise ValidationError(_("A stage cannot appear twice in the same route."))
            if len(route.line_ids) < 2:
                raise ValidationError(_("A route must have at least two stages."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "line_ids" in vals:
                # Check for uniqueness and minimum count before creating
                lines = vals["line_ids"]
                phase_ids = []
                count = 0
                for line in lines:
                    if line[0] == 0:  # Create
                        phase_ids.append(line[2]["phase_id"])
                        count += 1
                    elif line[0] == 4:  # Link
                        # This case is harder as we need to read from DB, but usually for new routes it's (0,0,...)
                        pass
                if len(phase_ids) != len(set(phase_ids)):
                    raise ValidationError(_("A stage cannot appear twice in the same route."))
                if count < 2:
                    raise ValidationError(_("A route must have at least two stages."))
        res = super().create(vals_list)
        return res

    def write(self, vals):
        res = super().write(vals)
        self._check_unique_stages()
        return res


class SaleOrderStageRouteLine(models.Model):
    _name = "sale.order.stage.route.line"
    _description = "Sale Order Stage Route Line"
    _order = "sequence"

    route_id = fields.Many2one("sale.order.stage.route", string="Route", ondelete="cascade", required=True)
    sequence = fields.Integer(default=10)
    phase_id = fields.Many2one("sale.order.phase", string="Stage", required=True)
