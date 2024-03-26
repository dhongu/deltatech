# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    direct_download = fields.Boolean()
