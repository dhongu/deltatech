from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    validation_date = fields.Date(string="Validation Date", readonly=True)

    def button_mark_done(self):
        # the parent may return a wizard (backorder, consumption...) before finishing the orders:
        # only the orders actually done by this call get the date
        to_finish = self.filtered(lambda production: production.state != "done")
        res = super().button_mark_done()
        for production in to_finish.filtered(lambda production: production.state == "done"):
            production.validation_date = fields.Date.context_today(production)
        return res
