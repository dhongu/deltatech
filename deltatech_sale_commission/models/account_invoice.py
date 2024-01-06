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

    def action_post(self):
        res = super().action_post()
        self.compute_purchase_price()
        return res


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    purchase_price = fields.Float(
        string="Cost Price",
        compute="_compute_purchase_price",
        digits="Product Price",
        store=True,
        readonly=False,
        groups="base.group_user",  # trebuie sa fie vizibil pentru a putea fi modificat
    )

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

    # se calculeaza pretul de achizitie din pretul de cost al produsului care se gaseste in SVL de la livrare
    def get_purchase_price(self):
        self.ensure_one()
        purchase_price = 0.0
        pickings = self.env["stock.picking"]
        for sale_line in self.sale_line_ids:
            pickings |= sale_line.order_id.picking_ids
        pickings = pickings.filtered(lambda p: p.state == "done")

        domain = [("picking_id", "in", pickings.ids), ("sale_line_id", "in", self.sale_line_ids.ids)]
        moves = self.env["stock.move"].search(domain)

        mrp_mod = self.env["ir.module.module"].sudo().search([("name", "=", "mrp"), ("state", "=", "installed")])
        if mrp_mod and self.product_id.bom_count:
            bom = self.product_id.bom_ids.filtered(lambda b: b.type == "phantom")
            if bom:
                purchase_price = 0
                for move in moves:
                    # get total value from svls
                    move_layers = move.with_context(active_test=False).mapped("stock_valuation_layer_ids")
                    move_price = 0
                    for layer in move_layers:
                        move_price += layer.value
                    purchase_price += abs(move_price)
                    # for a kit return, the number of moves linked to SO lines is increased by the size of the kit,
                    # so we have to adjust
                    kit_length = len(bom.bom_line_ids)
                move_length = len(moves)
                if kit_length != move_length:
                    factor = move_length / kit_length
                    purchase_price = purchase_price / factor
                # total value from svls computed, must divide by product qty
                if self.quantity:
                    purchase_price = purchase_price / self.quantity
        else:
            # preluare pret in svl
            svls = moves.with_context(active_test=False).mapped("stock_valuation_layer_ids")
            if hasattr(svls, "l10n_ro_invoice_line_id"):
                move_layers = svls.filtered(lambda l: l.l10n_ro_invoice_line_id == self)
                if move_layers:
                    purchase_price = 0.0
                    # add all layers
                    for svl in move_layers:
                        purchase_price += svl.value
                    if self.quantity:
                        purchase_price = abs(purchase_price / self.quantity)
                    else:
                        purchase_price = abs(purchase_price)
                else:
                    price_unit_list = svls.with_context(active_test=False).mapped("unit_cost")
                    if not price_unit_list:
                        price_unit_list = moves.mapped("price_unit")  # preturile din livare sunt negative
                    if price_unit_list:
                        purchase_price = abs(sum(price_unit_list)) / len(price_unit_list)
            else:
                price_unit_list = svls.with_context(active_test=False).mapped("unit_cost")
                if not price_unit_list:
                    price_unit_list = moves.mapped("price_unit")  # preturile din livare sunt negative
                if price_unit_list:
                    purchase_price = abs(sum(price_unit_list)) / len(price_unit_list)

            # daca e retur, ar trebui sa ia in calcul doar svl-urile de retur
            # if self.move_id.move_type == "out_refund":
            #     move_layers = moves.with_context(active_test=False).stock_valuation_layer_ids
            #     if hasattr(move_layers, "l10n_ro_invoice_line_id"):
            #         move_layers = move_layers.filtered(lambda l: l.l10n_ro_invoice_line_id == self)
            #         if move_layers:
            #             purchase_price = 0.0
            #             # add all layers
            #             for svl in move_layers:
            #                 purchase_price += svl.value
            #             if self.quantity:
            #                 purchase_price = purchase_price / self.quantity
        return purchase_price

    @api.depends("product_id", "company_id", "currency_id", "product_uom_id")
    def _compute_purchase_price(self):
        for invoice_line in self:
            # nu se calculeaza pretul de achizitie pentru liniile care nu sunt afisate in factura
            if invoice_line.exclude_from_invoice_tab or invoice_line.display_type:
                invoice_line.purchase_price = 0.0
                continue

            # nu se calculeaza pretul de achizitie pentru liniile care nu sunt legate de o comanda de vanzare
            if not invoice_line.sale_line_ids:
                invoice_line.purchase_price = 0.0
                continue

            # nu se calculeaza pretul de achizitie pentru liniile care nu sunt legate de un produs
            if not invoice_line.product_id:
                invoice_line.purchase_price = 0.0
                continue

            # nu se caluleaza pretul de achizitie pentru liniile care nu sunt legate de o factura de vanzare
            if invoice_line.move_id.move_type not in ["out_invoice", "out_refund"]:
                invoice_line.purchase_price = 0.0
                continue

            to_cur = self.env.user.company_id.currency_id
            product_uom = invoice_line.product_uom_id
            invoice_date = invoice_line.move_id.invoice_date or fields.Date.today()
            if invoice_line.sale_line_ids:
                # purchase_price = 0
                # for line in invoice_line.sale_line_ids:
                #     from_currency = line.order_id.currency_id
                #     price = line.product_uom._compute_price(line.purchase_price, product_uom)
                #     price = from_currency.with_context(date=invoice_date).compute(price, to_cur, round=False)
                #     purchase_price += price
                # purchase_price = purchase_price / len(invoice_line.sale_line_ids)

                #
                purchase_price = invoice_line.get_purchase_price()

            else:
                frm_cur = self.env.user.company_id.currency_id

                purchase_price = invoice_line.product_id.standard_price
                purchase_price = invoice_line.product_id.uom_id._compute_price(purchase_price, product_uom)

                purchase_price = frm_cur.with_context(date=invoice_date).compute(purchase_price, to_cur, round=False)
            # if invoice_line.move_id.move_type == "out_refund":
            #     purchase_price = -1 * purchase_price
            invoice_line.purchase_price = purchase_price

    # la salvare trebuie verificat pretul de achizitie
    def write(self, vals):
        if "purchase_price" in vals:
            self._check_sale_price()
        return super().write(vals)

    def _check_sale_price(self):
        for invoice_line in self:
            if not invoice_line.product_id:
                continue
            if invoice_line.exclude_from_invoice_tab or invoice_line.display_type:
                continue
            if invoice_line.move_id.move_type == "out_invoice":
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
