# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_assign(self, force_qty=False):
        res = super()._action_assign(force_qty=force_qty)
        if len(self) >= 1:
            self.inter_company_stock_update()
        return res

    def _action_done(self, cancel_backorder=False):
        moves_todo = super()._action_done(cancel_backorder)
        self.inter_company_stock_update()
        return moves_todo

    def inter_company_stock_update(self):
        current_company_partner = self.env.company.partner_id
        products = self.mapped("product_id")

        domain = [
            ("product_id", "in", products.ids),
            ("partner_id", "=", current_company_partner.id),
        ]
        supplierinfos = self.env["product.supplierinfo"].sudo().search(domain)

        for product in products:
            supplierinfo = supplierinfos.filtered(lambda s: s.product_id == product)
            if supplierinfo:
                supplierinfo.write({"qty_available": product.free_qty})
