# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    date_planned = fields.Datetime(
        "Scheduled Date", default=fields.Datetime.now, required=True, index=True, track_visibility="onchange"
    )
