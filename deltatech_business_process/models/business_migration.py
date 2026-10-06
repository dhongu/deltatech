# ©  2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models

from ..tools.display_name import code_display_name


class BusinessMigration(models.Model):
    _name = "business.migration"
    _description = "Migration data"
    _rec_names_search = ["name", "code"]

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code")
    area_id = fields.Many2one("business.area", string="Business Area")
    migration_tool = fields.Char(string="Migration Tool")
    migration_steps = fields.Char(string="Migration Steps")
    status = fields.Selection(
        [
            ("prepare", "Prepare"),
            ("migrate", "Migrate"),
            ("verify", "Verify"),
            ("done", "Done"),
        ],
        string="Status",
        default="prepare",
    )
    responsible_id = fields.Many2one(
        string="Responsible",
        domain="[('is_company', '=', False)]",
        comodel_name="res.partner",
    )

    project_id = fields.Many2one(string="Project", comodel_name="business.project", required=True)
    prepare_date = fields.Date(string="Prepare Date")
    migrate_date = fields.Date(string="Migrate Date")

    @api.depends("code", "name")
    @api.depends_context("formatted_display_name")
    def _compute_display_name(self):
        for migration in self:
            migration.display_name = code_display_name(migration)


class BusinessMigrationTest(models.Model):
    _name = "business.migration.test"
    _description = "Migration test"

    name = fields.Char(string="Name", required=True)
    migration_id = fields.Many2one(string="Migration", comodel_name="business.migration", required=True)

    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date")
