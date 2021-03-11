# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    vendor_qty_available = fields.Float(
        "Vendor Quantity Available", digits="Product Unit of Measure", compute="_compute_qty_at_date"
    )

    def _compute_qty_at_date(self):
        super(SaleOrderLine, self)._compute_qty_at_date()
        treated = self.browse()
        for line in self:
            if not line.display_qty_widget:
                continue
            qty_available = 0
            if line.product_id.seller_ids:
                for vendor in line.product_id.seller_ids:
                    qty_available += vendor.qty_available
                line.vendor_qty_available = vendor.qty_available
                treated |= line
        remaining = self - treated
        remaining.vendor_qty_available = False
