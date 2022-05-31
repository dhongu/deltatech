# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, models
from odoo.tools import float_compare, float_round


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def fix_qty_multiple(self, product, product_uom, qty=None):
        if qty is None:
            qty = 0

        if product.qty_multiple and product.qty_multiple != 1:
            qty_multiple = product.qty_multiple
            remainder = qty % qty_multiple

            if float_compare(remainder, 0.0, precision_rounding=product_uom.rounding) > 0:
                qty += qty_multiple - remainder

            if float_compare(qty, 0.0, precision_rounding=product_uom.rounding) > 0:
                qty = float_round(qty, precision_rounding=product_uom.rounding)
        if product.qty_minim and product.qty_minim > 0:
            if qty < product.qty_minim:
                qty = product.qty_minim

        return qty

    @api.onchange("product_uom_qty", "product_id")
    def _onchange_product_uom_qty(self):
        product_uom = self.product_uom or self.product_id.uom_id
        self.product_uom_qty = self.fix_qty_multiple(self.product_id, product_uom, self.product_uom_qty)
        # super(SaleOrderLine, self)._onchange_product_uom_qty()

    def write(self, vals):
        if len(self) == 1 and "product_uom_qty" in vals:
            if "product_id" in vals:
                product = self.env["product.product"].browse(vals["product_id"])
            else:
                product = self.product_id
            if "product_uom" in vals:
                product_uom = self.env["uom.uom"].browse(vals["product_uom"])
            else:
                product_uom = self.product_uom
            vals["product_uom_qty"] = self.fix_qty_multiple(product, product_uom, vals["product_uom_qty"])

        super(SaleOrderLine, self).write(vals)
