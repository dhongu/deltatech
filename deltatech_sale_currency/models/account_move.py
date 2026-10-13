# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange("invoice_date", "currency_id")
    def _onchange_invoice_date(self):
        date_eval = self.invoice_date or fields.Date.context_today(self)
        to_currency = self.currency_id
        company = self.company_id
        for line in self.invoice_line_ids:
            if line.display_type == "product":
                from_currency = self.currency_id
                price_unit = line.price_unit
                if line.sale_line_ids:
                    from_currency = line.sale_line_ids.mapped("currency_id")
                    sale_line = line.sale_line_ids[0]
                    price_unit = sale_line.price_unit
                    # the sale price is expressed in the sale line UoM; bring it
                    # into the invoice line UoM before the currency conversion
                    if sale_line.product_uom_id and line.product_uom_id:
                        price_unit = sale_line.product_uom_id._compute_price(price_unit, line.product_uom_id)
                if len(from_currency) > 1:
                    raise UserError(self.env._("You cannot have multiple currencies in the same invoice line."))

                price_unit = from_currency._convert(price_unit, to_currency, company, date_eval)
                line.price_unit = price_unit
