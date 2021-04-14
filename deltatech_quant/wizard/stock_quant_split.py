# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class StockQuantSplit(models.TransientModel):
    _name = "stock.quant.split"
    _description = "Stock Quant Split"

    parts = fields.Float(string="Parts")

    @api.model
    def default_get(self, fields_list):
        defaults = super(StockQuantSplit, self).default_get(fields_list)
        active_id = self.env.context.get("active_id", False)
        if active_id:
            quant = self.env["stock.quant"].browse(active_id)
            defaults["parts"] = quant.qty
        return defaults

    @api.multi
    def do_split(self):
        active_id = self.env.context.get("active_id", False)

        if active_id:
            quant = self.env["stock.quant"].browse(active_id)

            part = quant.qty / self.parts

            while quant:
                quant = self.env["stock.quant"]._quant_split(quant, part)
