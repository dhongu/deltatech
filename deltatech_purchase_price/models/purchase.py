# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _add_supplier_to_product(self):
        # todo: de adaugat parametru in configurare
        get_param = self.env["ir.config_parameter"].sudo().get_param
        add_supplier_to_product = safe_eval(get_param("purchase.add_supplier_to_product", "False"))
        if add_supplier_to_product:
            return super()._add_supplier_to_product()

    def button_confirm(self):
        self = self.with_context(from_po_confirmation=True)
        res = super().button_confirm()
        get_param = self.env["ir.config_parameter"].sudo().get_param
        force_price = safe_eval(get_param("purchase.force_price_at_validation", "False"))
        if force_price:
            for purchase_order in self:
                from_currency = purchase_order.currency_id
                company = purchase_order.company_id
                for line in purchase_order.order_line:
                    seller_ids = line.product_id.seller_ids or line.product_id.product_tmpl_id.seller_ids
                    price_unit = line.price_unit
                    for seller in seller_ids:
                        if seller.partner_id == purchase_order.partner_id.commercial_partner_id:
                            to_currency = seller.currency_id or self.env.user.company_id.currency_id
                            seller_price_unit = from_currency._convert(
                                price_unit,
                                to_currency,
                                company,
                                fields.Date.today(),
                            )
                            if line.product_id.product_tmpl_id.uom_po_id != line.product_uom:
                                default_uom = line.product_id.product_tmpl_id.uom_po_id
                                seller_price_unit = line.product_uom._compute_price(seller_price_unit, default_uom)
                            seller.write({"price": seller_price_unit})
        return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _get_stock_move_price_unit(self):
        self.ensure_one()
        price_unit = super(PurchaseOrderLine, self.with_context(date=self.date_planned))._get_stock_move_price_unit()
        return price_unit
