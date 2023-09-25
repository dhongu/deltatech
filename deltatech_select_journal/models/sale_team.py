# See README.rst file on addons root folder for license details

from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = "crm.team"

    journal_id = fields.Many2one("account.journal", domain=[("type", "=", "sale")])
