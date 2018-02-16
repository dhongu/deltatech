# coding=utf-8
from odoo import models, fields, api, _


class Currency(models.Model):
    _inherit = "res.currency"

    @api.multi
    def _compute_current_rate(self):
        fix_rate = self.env.context.get('fix_rate', False)
        if fix_rate and len(self) == 1:
            self.rate = fix_rate
        else:
            super(Currency, self)._compute_current_rate()
