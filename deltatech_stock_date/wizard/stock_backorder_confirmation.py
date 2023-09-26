# ©  2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = "stock.backorder.confirmation"

    date = fields.Datetime(string="Date")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if "pick_ids" in res and res.get("pick_ids"):
            pick_ids = res["pick_ids"][0][2]
            picking = self.env["stock.picking"].browse(pick_ids)[0]
            if picking.forced_effective_date:
                res["date"] = picking.forced_effective_date
            else:
                res["date"] = self.env.context.get("force_period_date", fields.Datetime.now())
        return res

    def process(self):
        self.pick_ids.write({"date": self.date})
        res = super(StockBackorderConfirmation, self.with_context(force_period_date=self.date)).process()
        for picking in self.pick_ids:  # clear backorders effective date
            if picking.backorder_ids:
                for backorder in picking.backorder_ids:
                    backorder.write({"forced_effective_date": False})
        return res

    def process_cancel_backorder(self):
        self.pick_ids.write({"date": self.date})
        super(StockBackorderConfirmation, self.with_context(force_period_date=self.date)).process_cancel_backorder()
