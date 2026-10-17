# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    vendor_qty_available = fields.Float(
        "Vendor Quantity Available",
        digits="Product Unit of Measure",
        compute="_compute_vendor_qty_available",
    )
    other_qty_available = fields.Float("Other Quantity Available", compute="_compute_vendor_qty_available")

    @api.depends_context("company")
    def _compute_vendor_qty_available(self):
        self.other_qty_available = 0
        # vendor rows of the current company, of its parent companies or shared (without company)
        companies = self.env.company.parent_ids
        for product in self:
            qty_available = 0
            for vendor in product.seller_ids:
                if vendor.company_id and vendor.company_id not in companies:
                    continue
                if not vendor.product_id or vendor.product_id == product:
                    qty_available += vendor.qty_available
            product.vendor_qty_available = qty_available
