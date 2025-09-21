# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super().action_post()
        purchase_invoices = self.filtered(lambda inv: inv.move_type == "in_invoice")
        get_param = self.env["ir.config_parameter"].sudo().get_param
        force_price = safe_eval(get_param("purchase.force_price_at_validation", "False"))
        if purchase_invoices and force_price:
            for move in purchase_invoices:
                from_currency = move.currency_id
                company = move.company_id
                for line in move.invoice_line_ids:
                    seller_ids = line.product_id.seller_ids or line.product_id.product_tmpl_id.seller_ids
                    price_unit = line.price_unit
                    for seller in seller_ids:
                        if seller.partner_id == move.partner_id.commercial_partner_id:
                            to_currency = seller.currency_id or self.env.user.company_id.currency_id
                            seller_price_unit = from_currency._convert(
                                price_unit,
                                to_currency,
                                company,
                                fields.Date.today(),
                            )
                            if line.product_id.product_tmpl_id.uom_po_id != line.product_uom_id:
                                default_uom = line.product_id.product_tmpl_id.uom_po_id
                                seller_price_unit = line.product_uom._compute_price(seller_price_unit, default_uom)
                            seller.write({"price": seller_price_unit})
        return res
