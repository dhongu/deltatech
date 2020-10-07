# ©  2008-2020  Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    request_id = fields.Many2one("maintenance.request", string="Maintenance Request")
    equipment_id = fields.Many2one("maintenance.equipment", string="Equipment")

    @api.model_create_multi
    def create(self, vals_list):
        pickings = super(StockPicking, self).create(vals_list)
        for picking in pickings:
            if picking.request_id:
                picking.request_id.write({"piking_id": picking.id})
        return pickings
