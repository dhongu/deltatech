# ©  2008-2020  Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    property_maintenance_picking_type = fields.Many2one(
        "stock.picking.type",
        related="company_id.property_maintenance_picking_type",
        string="Stock Operation Type for Maintenance",
    )
