# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super(SaleOrder, self)._create_invoices(grouped, final, date)

        for invoice in moves:
            to_currency = invoice.journal_id.currency_id or self.env.user.company_id.currency_id
            date_eval = date or invoice.invoice_date or fields.Date.context_today(self)
            from_currency = invoice.currency_id.with_context(date=date_eval)
            company = invoice.company_id
            if from_currency != to_currency:
                invoice.write({"currency_id": to_currency.id, "invoice_date": date_eval})

                for line in invoice.line_ids:
                    price_unit = from_currency._convert(line.price_unit, to_currency, company, date_eval)
                    amount_currency = from_currency._convert(line.amount_currency, to_currency, company, date_eval)
                    line.with_context(check_move_validity=False).write(
                        {"price_unit": price_unit, "currency_id": to_currency.id, "amount_currency": amount_currency}
                    )

                invoice._onchange_currency()
                invoice._recompute_dynamic_lines()
        return moves


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def unlink(self):
        product_id = self.env["ir.config_parameter"].sudo().get_param("sale.default_deposit_product_id")
        for line in self:
            if product_id and line.product_id.id == int(product_id) and line.qty_invoiced == 0:
                self -= line
                super(models.Model, line).unlink()
        return super(SaleOrderLine, self).unlink()
