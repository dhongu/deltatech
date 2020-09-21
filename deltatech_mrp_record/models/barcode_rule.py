# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.tools.translate import _


class BarcodeRule(models.Model):
    _inherit = "barcode.rule"

    type = fields.Selection(
        selection_add=[
            ("mrp_order", _("Production Order")),
            ("mrp_operation", _("Production Operation")),
            ("mrp_worker", _("Worker")),
            ("mrp_group", _("Work Order Group")),
        ]
    )
