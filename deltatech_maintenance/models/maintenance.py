# ©  2008-2020  Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models

import odoo.addons.decimal_precision as dp


class MaintenanceTeam(models.Model):
    _inherit = "maintenance.team"

    picking_type_id = fields.Many2one(
        "stock.picking.type", string="Picking Type", help="Stock Operation Type for Maintenance"
    )


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    partner_id = fields.Many2one("res.partner", string="Partner")
    component_ids = fields.One2many("maintenance.request.component", "request_id", string="Components", copy=True)
    operation_ids = fields.One2many("maintenance.request.operation", "request_id", string="Operations", copy=True)

    @api.multi
    def new_transfer_button(self):

        picking_type = self.maintenance_team_id.picking_type_id

        context = {
            "default_request_id": self.id,
            "default_equipment_id": self.equipment_id.id,
            "default_origin": self.name,
            "default_picking_type_id": picking_type.id,
            "default_partner_id": self.partner_id.id,
        }

        if self.component_ids:

            # picking = self.env["stock.picking"].with_context(context)

            context["default_move_ids_without_package"] = []

            for item in self.component_ids:
                value = self.env["stock.move"].default_get([])
                value.update(
                    {
                        "location_id": picking_type.default_location_src_id.id,
                        "location_dest_id": picking_type.default_location_dest_id.id,
                        "date_expected": self.schedule_date,
                        "product_id": item.product_id.id,
                        "product_uom_qty": item.quantity,
                        "product_uom": item.product_uom.id,
                        "name": item.product_id.name,
                        "state": "draft",
                    }
                )

                context["default_move_ids_without_package"] += [(0, 0, value)]

        return {
            "name": picking_type.name,
            "view_type": "form",
            "view_mode": "form",
            "res_model": "stock.picking",
            "view_id": False,
            "views": [[False, "form"]],
            "context": context,
            "type": "ir.actions.act_window",
        }

    @api.onchange("operation_ids")
    def onchange_operation_ids(self):
        if self.operation_ids:
            duration = 0
            for operation in self.operation_ids:
                duration += operation.duration
            self.duration = duration


class MaintenanceRequestComponent(models.Model):
    _name = "maintenance.request.component"
    _description = "Maintenance Request Component"

    request_id = fields.Many2one("maintenance.request", string="Request", readonly=True)
    product_id = fields.Many2one("product.product", string="Product")
    quantity = fields.Float(string="Quantity", digits=dp.get_precision("Product Unit of Measure"), default=1)
    product_uom = fields.Many2one("uom.uom", string="Unit of Measure ")
    note = fields.Char(string="Note")

    @api.onchange("product_id")
    def onchange_product_id(self):
        self.product_uom = self.product_id.uom_id


class MaintenanceRequestOperation(models.Model):
    _name = "maintenance.request.operation"
    _description = "Maintenance Request Operation"

    request_id = fields.Many2one("maintenance.request", string="Order", readonly=True)
    operation_id = fields.Many2one("maintenance.operation", string="Operation")
    duration = fields.Float(string="Duration")

    @api.onchange("operation_id")
    def onchange_operation_id(self):
        self.duration = self.operation_id.duration


class MaintenanceOperation(models.Model):
    _name = "maintenance.operation"
    _description = "Maintenance Operation"

    name = fields.Char(string="Operation")
    code = fields.Char(string="Code")
    duration = fields.Float(string="Duration")
    display_name = fields.Char(compute="_compute_display_name")

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, self.display_name))
        return result

    @api.depends("name", "code")  # this definition is recursive
    def _compute_display_name(self):
        for operation in self:
            if operation.code:
                operation.display_name = "[%s] %s" % (operation.code, operation.name)
            else:
                operation.display_name = operation.name
