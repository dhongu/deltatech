# ©  2008-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class Sequence(models.Model):
    _inherit = "ir.sequence"

    number_first = fields.Integer("First Number")
    number_last = fields.Integer("Last Number")

    def _next(self):
        if self.number_next_actual > self.number_last and self.number_last:
            raise ValidationError("The range of numbers has reached its maximum value")
        return super(Sequence, self)._next()
