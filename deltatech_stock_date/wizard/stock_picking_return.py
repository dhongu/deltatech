# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    date = fields.Datetime(string="Date")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res["date"] = self.env.context.get("force_period_date", fields.Datetime.now())
        return res

    def _prepare_move_default_values(self, return_line, new_picking):
        vals = super()._prepare_move_default_values(return_line, new_picking)
        vals["date"] = self.date
        return vals

    def _prepare_picking_default_values(self):
        vals = super()._prepare_picking_default_values()
        vals["date"] = self.date
        return vals
