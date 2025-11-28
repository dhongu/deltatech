# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    pricelist_id = fields.Many2one(
        "product.pricelist",
        string="Pricelist",
        help="Pricelist to use by default when creating Sales Orders from this project.",
    )

    def action_view_sos(self):
        self.ensure_one()
        action = super().action_view_sos()
        # When creating a SO from the project, propose the project's pricelist by default
        ctx = action.get("context") or {}
        if self.pricelist_id:
            # Do not override if a default_pricelist_id is already set upstream
            ctx = {**ctx, "default_pricelist_id": ctx.get("default_pricelist_id") or self.pricelist_id.id}
        action["context"] = ctx
        return action
