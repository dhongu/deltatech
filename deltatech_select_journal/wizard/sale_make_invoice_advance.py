# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    journal_id = fields.Many2one("account.journal", string="Journal", domain="[('type', '=', 'sale')]")
    order_id = fields.Many2one("sale.order")
    payment_term_id = fields.Many2one("account.payment.term", string="Payment Terms")
    is_currency_rate_custom = fields.Boolean(string="Custom currency rate", default=False)
    currency_rate = fields.Float(digits=(6, 4))

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if self._context.get("active_ids"):
            order = self.env["sale.order"].browse(self._context.get("active_ids"))[0]
            defaults["order_id"] = order.id
            if "payment_term_id" in fields_list:
                defaults["payment_term_id"] = order.payment_term_id.id
            # defaults['advance_payment_method'] = self._get_advance_payment_method()

            if order.payment_term_id and order.payment_term_id.line_ids[0].value == "percent":
                # defaults['payment_term_id'] = self.env.ref('account.account_payment_term_immediate').id
                if order.invoice_count == 0:
                    if "advance_payment_method" in fields_list:
                        defaults["advance_payment_method"] = "percentage"
                    if "amount" in fields_list:
                        defaults["amount"] = order.payment_term_id.line_ids[0].value_amount

            if "journal_id" in fields_list:
                journal = order.journal_id or order.team_id.journal_id
                if not journal:
                    company_id = self._context.get("company_id", self.env.user.company_id.id)
                    domain = [("type", "=", "sale"), ("company_id", "=", company_id)]
                    journal = self.env["account.journal"].search(domain, limit=1)
                if journal:
                    defaults["journal_id"] = journal.id
        return defaults

    def create_invoices(self):
        self.order_id.write({"journal_id": self.journal_id.id})
        if self.is_currency_rate_custom:
            new_self = self.with_context(default_journal_id=self.journal_id.id, currency_rate=self.currency_rate)
        else:
            new_self = self.with_context(default_journal_id=self.journal_id.id)
        return super(SaleAdvancePaymentInv, new_self).create_invoices()

    def _get_advance_details(self, order):
        amount, name = super()._get_advance_details(order)

        line_tax_type = self.env["ir.config_parameter"].sudo().get_param("account.show_line_subtotals_tax_selection")
        # de determinat tipul de tva
        if self.advance_payment_method == "percentage" and line_tax_type == "tax_included":
            amount = order.amount_total * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount)

        return amount, name

    def _create_invoice(self, order, so_line, amount):
        new_self = self.with_context(default_journal_id=self.journal_id.id)
        invoice = super(SaleAdvancePaymentInv, new_self)._create_invoice(order, so_line, amount)

        to_currency = self.journal_id.currency_id or self.env.user.company_id.currency_id
        date_eval = invoice.invoice_date or fields.Date.context_today(self)
        from_currency = invoice.currency_id.with_context(date=date_eval)

        if from_currency != to_currency:
            invoice.write({"currency_id": to_currency.id, "invoice_date": date_eval})
            if self.advance_payment_method != "fixed":
                for line in invoice.invoice_line_ids:
                    price_unit = from_currency.with_context(currency_rate=self.currency_rate)._convert(
                        line.price_unit, to_currency, invoice.company_id, date_eval
                    )
                    line.with_context(check_move_validity=False).write(
                        {"price_unit": price_unit, "currency_id": to_currency.id}
                    )
                invoice.with_context(check_move_validity=False)._recompute_dynamic_lines()
            else:
                for line in invoice.invoice_line_ids:
                    # taxes = line.product_id.taxes_id or line.tax_ids
                    price_w_taxes = self.fixed_amount
                    # for tax in taxes:
                    #     price_w_taxes = self.fixed_amount / (1 + tax.amount / 100)
                    invoice_price = to_currency.with_context(currency_rate=self.currency_rate)._convert(
                        price_w_taxes, from_currency, invoice.company_id, date_eval
                    )
                    line.with_context(check_move_validity=False).write(
                        {"price_unit": invoice_price, "currency_id": to_currency.id}
                    )
                    # price_unit_saleorder = to_currency.with_context(currency_rate=self.currency_rate)._convert(
                    #     self.fixed_amount, from_currency, invoice.company_id, date_eval
                    # )
                    # sale_orders = self.env["sale.order"].browse(self._context.get("active_ids", []))
                    # order_line_downpayment = False
                    # for order in sale_orders:
                    #     order_lines = order.order_line
                    #     for order_line in order_lines:
                    #         if order_line.is_downpayment:
                    #             # order_line.write({'price_unit': price_unit_saleorder})
                    #             order_line_downpayment = order_line
                    # if order_line_downpayment:
                    #     order_line_downpayment.write({"price_unit": price_unit_saleorder})

                invoice.with_context(check_move_validity=False)._recompute_dynamic_lines()
                # invoice._compute_tax_totals_json() #Todo: mai exista metoda aceasta in 16 ?

        if self.advance_payment_method == "percentage":
            invoice.write({"invoice_payment_term_id": False})
        else:
            invoice.write({"invoice_payment_term_id": self.payment_term_id.id})
            invoice.write({"invoice_date": False})
        if self.currency_rate:
            invoice.write({"currency_rate_custom": self.currency_rate or 1})
        return invoice

    @api.onchange("advance_payment_method")
    def onchange_advance_payment_method(self):
        if self.advance_payment_method == "percentage":
            amount = 0.0
            order = self.order_id
            if order.payment_term_id and order.payment_term_id.line_ids[0].value == "percent":
                amount = order.payment_term_id.line_ids[0].value_amount
            return {"value": {"amount": amount}}
        return {}

    @api.onchange("journal_id")
    def onchange_journal_id(self):
        company = self.order_id.company_id
        journal_currency = self.journal_id.currency_id or company.currency_id
        from_currency = self.order_id.currency_id
        self.currency_rate = from_currency._convert(1, journal_currency, company, fields.Date.context_today(self))
