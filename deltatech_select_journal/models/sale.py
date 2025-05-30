# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        journal_id = res.get("journal_id", self.journal_id.id or self.team_id.journal_id.id)
        if journal_id:
            journal = self.env["account.journal"].browse(journal_id)
            to_currency = journal.currency_id
            if res.get("currency_id", False) != to_currency.id:
                res["currency_id"] = journal.currency_id.id or self.env.user.company_id.currency_id.id
        currency_rate = self.env.context.get("currency_rate", False)
        if currency_rate:
            res["currency_rate_custom"] = currency_rate
        return res


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def unlink(self):
        product_id = self.env["ir.config_parameter"].sudo().get_param("sale.default_deposit_product_id")
        for line in self:
            if product_id and line.product_id.id == int(product_id) and line.qty_invoiced == 0:
                self -= line
                super(models.Model, line).unlink()
        return super().unlink()

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        company = self.order_id.company_id
        journal_id = self.env.context.get("default_journal_id", False)
        if journal_id:
            journal = self.env["account.journal"].browse(journal_id)
            to_currency = journal.currency_id or company.currency_id
            from_currency = self.order_id.pricelist_id.currency_id
            date_eval = fields.Date.context_today(self)
            price_unit = from_currency._convert(res["price_unit"], to_currency, company, date_eval)
            res["price_unit"] = price_unit
        return res
