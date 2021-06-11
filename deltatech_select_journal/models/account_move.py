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
                invoice = line.move_id
                date_eval = invoice.invoice_date
                from_currency = invoice.currency_id
                for sale_line in line.sale_line_ids:
                    to_currency = sale_line.order_id.currency_id
                    price_unit = from_currency._convert(line.price_unit, to_currency, invoice.company_id, date_eval)
                    sale_line.write({"price_unit": price_unit})

            except UserError:
                pass
        return res
