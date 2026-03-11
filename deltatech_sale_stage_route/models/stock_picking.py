# © 2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    stage_route_id = fields.Many2one(
        "sale.order.stage.route", related="sale_id.stage_route_id", string="Stage Route", store=True
    )
    phase_id = fields.Many2one(
        "sale.order.phase",
        string="Phase",
        related="sale_id.phase_id",
        store=True,
        readonly=False,
        group_expand="_read_group_phase_ids",
    )
    phase_color = fields.Integer(related="phase_id.color", string="Phase Color")
    phase_ids = fields.Many2many("sale.order.phase", string="Phases", related="sale_id.phase_ids")
    next_phase_id = fields.Many2one("sale.order.phase", string="Next Phase", compute="_compute_next_phase_id")
    next_phase_color = fields.Integer(related="next_phase_id.color", string="Next Phase Color")

    def write(self, vals):
        if "phase_id" in vals:
            # Check if user is phase admin
            is_phase_admin = self.env.user.has_group("deltatech_sale_stage_route.group_phase_admin")
            if not is_phase_admin:
                for picking in self:
                    new_phase_id = vals.get("phase_id")
                    if picking.phase_id.id != new_phase_id:
                        if picking.stage_route_id:
                            # Only allow moving to next stage
                            # We use sudo() to check the next stage because the current user might not have
                            # read access to the stage route lines (e.g. they are only a warehouse user)
                            if new_phase_id != picking.sudo().next_phase_id.id:
                                raise ValidationError(
                                    _(
                                        "You are not allowed to move the picking to this stage. "
                                        "Only a Phase Admin can perform non-sequential moves."
                                    )
                                )
                        else:
                            # If no route, maybe allow change if they are not admin?
                            # The requirement says "only phase admins will be able to move a picking in a stage that is not the next stage"
                            # If there is no route, there is no "next stage".
                            # In this case, maybe they shouldn't be able to move it at all?
                            # For now, let's stick to the route logic.
                            pass
        return super().write(vals)

    @api.model
    def _read_group_phase_ids(self, phases, domain):
        return self.env["sale.order.phase"].search([])

    def _compute_next_phase_id(self):
        for picking in self:
            next_phase = False
            if picking.phase_id and picking.stage_route_id:
                route_lines = picking.stage_route_id.line_ids.sorted("sequence")
                phases = route_lines.mapped("phase_id")
                if picking.phase_id in phases:
                    current_index = phases.ids.index(picking.phase_id.id)
                    if current_index < len(phases) - 1:
                        next_phase = phases[current_index + 1]
            picking.next_phase_id = next_phase

    def _get_fields_stock_barcode(self):
        res = super()._get_fields_stock_barcode()
        res.append("phase_id")
        return res

    def _get_stock_barcode_data(self):
        res = super()._get_stock_barcode_data()
        picking_ids = [p["id"] for p in res["records"]["stock.picking"]]
        pickings = self.browse(picking_ids)
        phases_data = {
            p.phase_id.id: {"display_name": p.phase_id.display_name, "color": p.phase_id.color}
            for p in pickings
            if p.phase_id
        }

        # Calculate next phase data
        next_phases_data = {}
        for picking in pickings:
            if picking.next_phase_id:
                next_phases_data[picking.id] = {
                    "id": picking.next_phase_id.id,
                    "display_name": picking.next_phase_id.display_name,
                    "color": picking.next_phase_id.color,
                }

        for picking_data in res["records"]["stock.picking"]:
            p_id = picking_data.get("phase_id")
            if p_id and isinstance(p_id, int) and p_id in phases_data:
                picking_data["phase_id"] = {
                    "id": p_id,
                    "display_name": phases_data[p_id]["display_name"],
                    "color": phases_data[p_id]["color"],
                }

            pk_id = picking_data.get("id")
            if pk_id in next_phases_data:
                picking_data["next_phase_id"] = next_phases_data[pk_id]

        return res

    def button_validate(self):
        pickings_to_validate = self.env["stock.picking"]
        advanced_pickings = self.env["stock.picking"]
        for picking in self:
            if picking.stage_route_id:
                # check if it is the last stage
                current_phase = picking.sale_id.phase_id
                route_lines = picking.stage_route_id.line_ids.sorted("sequence")
                phases = route_lines.mapped("phase_id")
                if current_phase in phases:
                    current_index = phases.ids.index(current_phase.id)
                    if current_index < len(phases) - 1:
                        # not last stage, move to next
                        next_phase = phases[current_index + 1]
                        picking.sale_id.phase_id = next_phase
                        if current_index + 1 == len(phases) - 1:
                            # reached the last stage, also validate the picking
                            pickings_to_validate |= picking
                        else:
                            # advanced but not validated, reset quantities for next user
                            picking.move_line_ids.write({"quantity": 0.0, "picked": False})
                            picking.action_assign()
                            advanced_pickings |= picking
                    else:
                        # last stage, validate
                        pickings_to_validate |= picking
                else:
                    raise UserError(_("The current phase of the sale order is not in the assigned route."))
            else:
                pickings_to_validate |= picking

        res = True
        if pickings_to_validate:
            res = super(StockPicking, pickings_to_validate).button_validate()

        if advanced_pickings and not pickings_to_validate:
            # If we only advanced and didn't validate, we want to close the barcode view.
            # In Odoo 18 Barcode app, returning a client action is the best way to exit.
            # Redirecting to the picking list (Operations) provides a better user experience than the main menu.
            return self.env.ref("stock_barcode.stock_picking_action_kanban").read()[0]

        return res
