# ©  2017-2019 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    purchase_price = fields.Float(string="Cost", digits="Product Price")
    sale_user_id = fields.Many2one("res.users", string="Salesperson", compute="_compute_sale_user_id", store=True)

    commission = fields.Float(string="Commission", default=0.0)

    @api.depends("sale_line_ids")
    def _compute_sale_user_id(self):
        for line in self:
            if line.sale_line_ids:
                line.sale_user_id = line.sale_line_ids[0].order_id.user_id
            else:
                line.sale_user_id = False

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

    @api.depends("product_id", "company_id", "currency_id", "product_uom_id")
    def _compute_purchase_price(self):
        for invoice_line in self:
            if invoice_line.exclude_from_invoice_tab or invoice_line.display_type:
                invoice_line.purchase_price = 0.0
                continue
            if not invoice_line.product_id:
                invoice_line.purchase_price = 0.0
                continue
            if invoice_line.move_id.type not in ["out_invoice", "out_refund"]:
                invoice_line.purchase_price = 0.0
                continue

            to_cur = self.env.user.company_id.currency_id
            product_uom = invoice_line.product_uom_id
            invoice_date = invoice_line.move_id.invoice_date or fields.Date.today()
            if invoice_line.sale_line_ids:
                purchase_price = 0
                for line in invoice_line.sale_line_ids:
                    from_currency = line.order_id.currency_id
                    price = line.product_uom._compute_price(line.purchase_price, product_uom)
                    price = from_currency.with_context(date=invoice_date).compute(price, to_cur, round=False)
                    purchase_price += price
                purchase_price = purchase_price / len(invoice_line.sale_line_ids)
            else:
                frm_cur = self.env.user.company_id.currency_id

                purchase_price = invoice_line.product_id.standard_price
                purchase_price = invoice_line.product_id.uom_id._compute_price(purchase_price, product_uom)

                purchase_price = frm_cur.with_context(date=invoice_date).compute(purchase_price, to_cur, round=False)
            if invoice_line.move_id.type == "out_refund":
                purchase_price = -1 * purchase_price
            invoice_line.purchase_price = purchase_price

    @api.constrains("price_unit", "purchase_price")
    def _check_sale_price(self):
        for invoice_line in self:
            if not invoice_line.product_id:
                continue
            if invoice_line.exclude_from_invoice_tab or invoice_line.display_type:
                continue
            if invoice_line.move_id.type == "out_invoice":
                if not self.env.user.has_group("deltatech_sale_margin.group_sale_below_purchase_price"):
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

    @api.onchange("product_id")
    def _onchange_product_id(self):

        res = super(AccountInvoiceLine, self)._onchange_product_id()
        self._compute_purchase_price()
        return res

    @api.model
    def create(self, vals):
        if "purchase_price" not in vals and ("display_type" not in vals or not vals["display_type"]):
            move_id = self.env["account.move"].browse(vals["move_id"])
            product_id = self.env["product.product"].browse(vals["product_id"])
            product_uom_id = self.env["uom.uom"].browse(vals["product_uom_id"])

            vals["purchase_price"] = self._compute_margin(move_id, product_id, product_uom_id)

        return super(AccountInvoiceLine, self).create(vals)
