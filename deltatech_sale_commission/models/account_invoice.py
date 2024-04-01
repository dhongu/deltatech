# ©  2017-2019 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = "account.move"

    def compute_purchase_price(self):
        for invoice in self:
            for invoice_line in invoice.invoice_line_ids:
                purchase_price = invoice_line.get_purchase_price()
                invoice_line.write({"purchase_price": purchase_price})


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    sale_user_id = fields.Many2one("res.users", string="Salesperson", compute="_compute_sale_user_id", store=True)

    purchase_price = fields.Float(
        string="Cost Price",
        compute="_compute_purchase_price",
        digits="Product Price",
        store=True,
        readonly=False,
        groups="base.group_user",
    )

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

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if vals.get("exclude_from_invoice_tab", False) or vals.get("display_type", False):
    #             continue
    #         if "purchase_price" not in vals:
    #             invoice_id = self.env["account.move"].browse(vals["move_id"])
    #             if "product_id" in vals:
    #                 product_id = self.env["product.product"].browse(vals["product_id"])
    #                 uom_id = self.env["uom.uom"].browse(vals["product_uom_id"])
    #                 vals["purchase_price"] = self._compute_margin(invoice_id, product_id, uom_id)
    #
    #     return super(AccountInvoiceLine, self).create(vals_list)

    def get_purchase_price(self):
        self.ensure_one()
        purchase_price = 0.0
        pickings = self.env["stock.picking"]
        for sale_line in self.sale_line_ids:
            pickings |= sale_line.order_id.picking_ids

        domain = [("picking_id", "in", pickings.ids), ("sale_line_id", "in", self.sale_line_ids.ids)]
        moves = self.env["stock.move"].search(domain)

        mrp_mod = self.env["ir.module.module"].search([("name", "=", "mrp"), ("state", "=", "installed")])
        if mrp_mod and self.product_id.bom_count:
            bom = self.product_id.variant_bom_ids.filtered(lambda b: b.type == "phantom")
            purchase_price = 0
            for move in moves:
                bom_line = bom.bom_line_ids.filtered(lambda b: b.product_id == move.product_id)
                price_unit_comp = move.mapped("stock_valuation_layer_ids").mapped("unit_cost")
                purchase_price += sum(price_unit_comp) * bom_line.product_qty
        else:
            # preluare pret in svl
            svls = moves.mapped("stock_valuation_layer_ids")
            price_unit_list = svls.mapped("unit_cost")
            if not price_unit_list:
                price_unit_list = moves.mapped("price_unit")  # preturile din livare sunt negative
            if price_unit_list:
                purchase_price = abs(sum(price_unit_list)) / len(price_unit_list)

        return purchase_price

    @api.depends("product_id", "company_id", "currency_id", "product_uom_id")
    def _compute_purchase_price(self):
        deposit_product = self.env["ir.config_parameter"].sudo().get_param("sale.default_deposit_product_id")
        for invoice_line in self:
            if invoice_line.display_type != "product":
                invoice_line.purchase_price = 0.0
                continue
            if not invoice_line.product_id:
                invoice_line.purchase_price = 0.0
                continue
            if invoice_line.move_id.move_type not in ["out_invoice", "out_refund"]:
                invoice_line.purchase_price = 0.0
                continue
            if invoice_line.product_id.id == int(deposit_product):
                invoice_line.purchase_price = invoice_line.price_unit
                continue

            to_cur = self.env.user.company_id.currency_id
            company = self.env.user.company_id
            product_uom = invoice_line.product_uom_id
            invoice_date = invoice_line.move_id.invoice_date or fields.Date.today()
            if invoice_line.sale_line_ids:
                purchase_price = 0
                for line in invoice_line.sale_line_ids:
                    from_currency = line.order_id.currency_id
                    price = line.product_uom._compute_price(line.purchase_price, product_uom)
                    price = from_currency._convert(price, to_cur, company, invoice_date, round=False)
                    purchase_price += price
                purchase_price = purchase_price / len(invoice_line.sale_line_ids)

                purchase_price = invoice_line.get_purchase_price()

            else:
                frm_cur = self.env.user.company_id.currency_id

                purchase_price = invoice_line.product_id.standard_price
                purchase_price = invoice_line.product_id.uom_id._compute_price(purchase_price, product_uom)

                purchase_price = frm_cur._convert(purchase_price, to_cur, company, invoice_date, round=False)
            # if invoice_line.move_id.move_type == "out_refund":
            #     purchase_price = -1 * purchase_price
            invoice_line.purchase_price = purchase_price

    @api.constrains("price_unit", "purchase_price")
    def _check_sale_price(self):
        for invoice_line in self:
            if not invoice_line.product_id:
                continue
            if invoice_line.display_type != "product":
                continue
            if invoice_line.move_id.move_type == "out_invoice":
                if not self.env.user.has_group("deltatech_sale_margin.group_sale_below_purchase_price"):
                    date_eval = invoice_line.move_id.invoice_date or fields.Date.context_today(invoice_line)
                    if (
                        invoice_line.move_id.currency_id
                        and invoice_line.move_id.currency_id.id != self.env.user.company_id.currency_id.id
                    ):
                        from_currency = invoice_line.move_id.currency_id.with_context(date=date_eval)
                        to_currency = invoice_line.env.user.company_id.currency_id
                        company = invoice_line.env.user.company_id
                        price_unit = from_currency._convert(
                            from_amount=invoice_line.price_unit,
                            to_currency=to_currency,
                            company=company,
                            date=date_eval,
                        )
                    else:
                        price_unit = invoice_line.price_unit
                    if 0 < price_unit < invoice_line.purchase_price and invoice_line.move_id.state in ["draft"]:
                        raise UserError(_("You can not sell below the purchase price."))
