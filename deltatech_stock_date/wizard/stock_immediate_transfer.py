# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class StockImmediateTransfer(models.TransientModel):
    _inherit = "stock.immediate.transfer"

    date = fields.Datetime(string="Date")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # res["date"] = self.env.context.get("force_period_date", fields.Datetime.now())
        if "pick_ids" in res and res.get("pick_ids"):
            pick_ids = res["pick_ids"][0][2]
            picking = self.env["stock.picking"].browse(pick_ids)[0]
            if picking.forced_effective_date:
                res["date"] = picking.forced_effective_date
            else:
                res["date"] = self.env.context.get("force_period_date", fields.Datetime.now())
        return res

    def process(self):
        self.pick_ids.write({"date": self.date, "date_done": self.date})
        return super(StockImmediateTransfer, self.with_context(force_period_date=self.date)).process()
