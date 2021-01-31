# ©  2017-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models
from odoo.exceptions import Warning

import odoo.addons.decimal_precision as dp


class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"

    purchase_price = fields.Float(
        string="Cost Price", compute="_compute_purchase_price", store=True, digits=dp.get_precision("Product Price")
    )  # valoare stocului in moneda companiei
    commission = fields.Float(string="Commission", default=0.0)

    @api.depends("product_id")
    def _compute_purchase_price(self):
        for invoice_line in self:
            if invoice_line.product_id:
                to_cur = invoice_line.invoice_id.currency_id
                product_uom = invoice_line.uom_id
                date_invoice = invoice_line.invoice_id.date_invoice
                if invoice_line.sale_line_ids:
                    purchase_price = 0
                    for line in invoice_line.sale_line_ids:
                        from_currency = line.order_id.currency_id
                        price = line.product_uom._compute_price(line.purchase_price, product_uom)
                        price = from_currency.with_context(date=date_invoice).compute(price, to_cur, round=False)
                        purchase_price += price
                    purchase_price = purchase_price / len(invoice_line.sale_line_ids)
                else:
                    frm_cur = self.env.user.company_id.currency_id

                    purchase_price = invoice_line.product_id.standard_price
                    purchase_price = invoice_line.product_id.uom_id._compute_price(purchase_price, product_uom)

                    purchase_price = frm_cur.with_context(date=date_invoice).compute(
                        purchase_price, to_cur, round=False
                    )

                invoice_line.purchase_price = purchase_price

    @api.constrains("price_unit", "purchase_price")
    def _check_sale_price(self):
        for invoice_line in self:
            if invoice_line.invoice_id.type == "out_invoice":
                if not self.env["res.users"].has_group("deltatech_sale_margin.group_sale_below_purchase_price"):
                    date_eval = invoice_line.invoice_id.date_invoice or fields.Date.context_today(invoice_line)
                    if (
                        invoice_line.invoice_id.currency_id
                        and invoice_line.invoice_id.currency_id.id != self.env.user.company_id.currency_id.id
                    ):
                        from_currency = invoice_line.invoice_id.currency_id.with_context(date=date_eval)
                        price_unit = from_currency.compute(
                            invoice_line.price_unit, invoice_line.env.user.company_id.currency_id
                        )
                    else:
                        price_unit = invoice_line.price_unit
                        if invoice_line.sale_line_ids:
                            if invoice_line.sale_line_ids[0].currency_id != invoice_line.currency_id:
                                from_currency = invoice_line.sale_line_ids[0].currency_id
                                to_cur = invoice_line.invoice_id.currency_id
                                price_unit = from_currency.with_context(date=date_eval).compute(price_unit, to_cur,
                                                                                                round=False)

                    if 0 < price_unit < invoice_line.purchase_price and invoice_line.invoice_id.state in ["draft"]:
                        raise Warning(_("You can not sell below the purchase price."))
