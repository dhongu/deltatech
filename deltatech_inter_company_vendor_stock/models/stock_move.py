# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_assign(self, force_qty=False):
        res = super()._action_assign(force_qty=force_qty)
        if self:
            self.inter_company_stock_update()
        return res

    def _action_done(self, cancel_backorder=False):
        moves_todo = super()._action_done(cancel_backorder)
        self.inter_company_stock_update()
        return moves_todo

    def inter_company_stock_update(self):
        """Write the free stock of the current company on the vendor lines where it is the vendor.

        A vendor line with a variant gets the free stock of that variant; a line on the template only
        (no variant, the usual case from the product form) gets the free stock of all its variants.
        """
        products = self.product_id
        if not products:
            return
        templates = products.product_tmpl_id
        domain = [
            ("partner_id", "=", self.env.company.partner_id.id),
            ("product_tmpl_id", "in", templates.ids),
            "|",
            ("product_id", "=", False),
            ("product_id", "in", products.ids),
        ]
        supplierinfos = self.env["product.supplierinfo"].sudo().search(domain)
        for supplierinfo in supplierinfos:
            if supplierinfo.product_id:
                qty = self.env["product.product"].browse(supplierinfo.product_id.id).free_qty
            else:
                variants = templates.filtered(
                    lambda t, s=supplierinfo: t.id == s.product_tmpl_id.id
                ).product_variant_ids
                qty = sum(variants.mapped("free_qty"))
            supplierinfo.qty_available = qty
