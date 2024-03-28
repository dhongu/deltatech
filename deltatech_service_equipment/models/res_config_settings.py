# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    picking_type_for_service = fields.Many2one(
        "stock.picking.type", string="Outgoing not to be invoiced", config_parameter="service.picking_type_for_service"
    )
