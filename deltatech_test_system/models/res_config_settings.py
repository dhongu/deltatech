# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    database_uuid = fields.Char(config_parameter="database.uuid")
    database_uuid_productive = fields.Char(config_parameter="database.uuid_productive")

    is_productive_system = fields.Boolean(
        string="Is Productive System",
        help="It is a productive system",
        compute="_compute_is_productive_system",
        inverse="_inverse_is_productive_system",
    )

    @api.depends("database_uuid", "database_uuid_productive")
    def _compute_is_productive_system(self):
        self.is_productive_system = self.database_uuid == self.database_uuid_productive

    def _inverse_is_productive_system(self):
        if self.is_productive_system:
            self.database_uuid_productive = self.database_uuid
        else:
            self.database_uuid_productive = False
