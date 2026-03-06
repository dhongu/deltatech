# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self):
        res = super()._prepare_invoice()

        currency = self.journal_id.currency_id or self.company_id.currency_id
        res["currency_id"] = currency.id

        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)

        if res.get("display_type") == "product":
            company = self.order_id.company_id
            journal = self.order_id.journal_id
            if journal:
                to_currency = journal.currency_id or company.currency_id
                from_currency = self.order_id.pricelist_id.currency_id
                date_eval = fields.Date.context_today(self)
                price_unit = from_currency._convert(res["price_unit"], to_currency, company, date_eval)
                res["price_unit"] = price_unit

        return res
