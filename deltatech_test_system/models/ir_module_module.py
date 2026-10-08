# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    database_is_neutralized = fields.Boolean(compute="_compute_database_is_neutralized")

    def _compute_database_is_neutralized(self):
        """Compute if the database is neutralized based on the ir.config_parameter value."""
        self.database_is_neutralized = self.env["ir.config_parameter"].sudo().get_bool("database.is_neutralized")
