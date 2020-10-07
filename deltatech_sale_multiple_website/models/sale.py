# ©  2008-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def fix_qty_multiple(self, product, product_uom, qty):

        if product.check_min_website:  # daca se face verificare doa in website
            if self.env.context.get("website_id"):
                qty = super(SaleOrderLine, self).fix_qty_multiple(product, product_uom, qty)
        else:
            qty = super(SaleOrderLine, self).fix_qty_multiple(product, product_uom, qty)

        return qty
