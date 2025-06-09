from datetime import date

from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    validation_date = fields.Date(string="Validation Date", readonly=True)

    def button_mark_done(self):
        res = super().button_mark_done()
        self.validation_date = date.today()
        return res
