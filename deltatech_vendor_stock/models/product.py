# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    vendor_qty_available = fields.Float(
        "Vendor Quantity Available", digits="Product Unit of Measure", compute="_compute_vendor_qty_available"
    )

    def _compute_vendor_qty_available(self):
        treated = self.env["product.product"]
        for product in self:
            qty_available = 0
            for vendor in product.seller_ids:
                qty_available += vendor.qty_available
            product.vendor_qty_available = qty_available
            treated |= product
        remaining = self - treated
        remaining.vendor_qty_available = False
