# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):

        res = super(AccountMove, self).action_post()
        line_ids = self.mapped("line_ids").filtered(lambda line: line.sale_line_ids.is_downpayment)
        for line in line_ids:
            try:
                line.sale_line_ids.tax_id = line.tax_ids
                line.sale_line_ids.price_unit = line.price_unit
            except UserError:
                pass
        return res
