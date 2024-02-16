# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

import odoo
from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    database_is_neutralized = fields.Boolean(config_parameter="database.is_neutralized")

    def get_installed_modules(self):
        self.env.cr.execute(
            """
            SELECT name
              FROM ir_module_module
             WHERE state IN ('installed', 'to upgrade', 'to remove');
        """
        )
        return [result[0] for result in self.env.cr.fetchall()]

    def get_neutralization_queries(self, modules):
        # neutralization for each module
        for module in modules:
            filename = odoo.modules.get_module_resource(module, "data/neutralize.sql")
            if filename:
                with odoo.tools.misc.file_open(filename) as file:
                    yield file.read().strip()

    def neutralize_database(self):
        installed_modules = self.get_installed_modules()
        queries = self.get_neutralization_queries(installed_modules)
        for query in queries:
            self.env.cr.execute(query)
        _logger.info("Neutralization finished")

    def set_values(self):
        super().set_values()
        if self.database_is_neutralized:
            self.neutralize_database()
