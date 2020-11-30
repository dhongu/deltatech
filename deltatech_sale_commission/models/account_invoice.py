# ©  2017-2019 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    purchase_price = fields.Float(
        string="Cost Price",
        # compute="_compute_purchase_price", store=True,
        digits="Product Price",
    )  # valoare stocului in moneda companiei
    commission = fields.Float(string="Commission", default=0.0)

    def _compute_margin(self, invoice_id, product_id, product_uom_id):
        frm_cur = self.env.user.company_id.currency_id
        to_cur = invoice_id.currency_id
        purchase_price = product_id.standard_price
        if product_uom_id != product_id.uom_id:
            purchase_price = product_id.uom_id._compute_price(purchase_price, product_uom_id)
        price = frm_cur._convert(
            purchase_price,
            to_cur,
            invoice_id.company_id or self.env.user.company_id,
            invoice_id.invoice_date or fields.Date.today(),
            round=False,
        )
        return price

    @api.model
    def create(self, vals):
        if "purchase_price" not in vals:
            invoice_id = self.env["account.move"].browse(vals["move_id"])
            product_id = self.env["product.product"].browse(vals["product_id"])
            uom_id = self.env["uom.uom"].browse(vals["product_uom_id"])
            vals["purchase_price"] = self._compute_margin(invoice_id, product_id, uom_id)

        return super(AccountInvoiceLine, self).create(vals)

    @api.depends("product_id")
    def _compute_purchase_price(self):
        for invoice_line in self:
            if invoice_line.invoice_id.move_type in ["out_invoice", "out_refund"] and invoice_line.product_id:
                to_cur = self.env.user.company_id.currency_id
                product_uom = invoice_line.product_uom_id
                date_invoice = invoice_line.invoice_id.date_invoice or fields.Date.today()
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
                if invoice_line.invoice_id.move_type == "out_refund":
                    purchase_price = -1 * purchase_price
                invoice_line.purchase_price = purchase_price

    @api.constrains("price_unit", "purchase_price")
    def _check_sale_price(self):
        for invoice_line in self:
            if invoice_line.move_id.move_type == "out_invoice":
                if not self.env["res.users"].has_group("deltatech_sale_margin.group_sale_below_purchase_price"):
                    date_eval = invoice_line.move_id.invoice_date or fields.Date.context_today(invoice_line)
                    if (
                        invoice_line.move_id.currency_id
                        and invoice_line.move_id.currency_id.id != self.env.user.company_id.currency_id.id
                    ):
                        from_currency = invoice_line.move_id.currency_id.with_context(date=date_eval)
                        price_unit = from_currency.compute(
                            invoice_line.price_unit, invoice_line.env.user.company_id.currency_id
                        )
                    else:
                        price_unit = invoice_line.price_unit
                    if 0 < price_unit < invoice_line.purchase_price and invoice_line.move_id.state in ["draft"]:
                        raise UserError(_("You can not sell below the purchase price."))
