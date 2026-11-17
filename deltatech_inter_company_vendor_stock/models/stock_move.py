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
        if not supplierinfos:
            return
        # free stock computed once, in the current company, for all the variants involved
        variants = products | templates.product_variant_ids
        free_qty = dict(zip(variants.ids, variants.mapped("free_qty"), strict=True))
        for supplierinfo in supplierinfos:
            if supplierinfo.product_id:
                qty = free_qty.get(supplierinfo.product_id.id, 0.0)
            else:
                qty = sum(
                    free_qty.get(variant_id, 0.0) for variant_id in supplierinfo.product_tmpl_id.product_variant_ids.ids
                )
            supplierinfo.qty_available = qty
