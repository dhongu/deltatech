# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ImportLinesWizard(models.TransientModel):
    _inherit = "import.lines.wizard"

    match_by = fields.Selection(
        selection_add=[("vendor_code", "Vendor Product Code")], ondelete={"vendor_code": "set default"}
    )


class ImportLinesMapping(models.Model):
    _inherit = "import.lines.mapping"

    match_by = fields.Selection(
        selection_add=[("vendor_code", "Vendor Product Code")], ondelete={"vendor_code": "set default"}
    )
