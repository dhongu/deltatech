# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    vendor_qty_available = fields.Float(
        "Vendor Quantity Available", digits="Product Unit of Measure", compute="_compute_qty_at_date"
    )
    other_qty_available = fields.Float(
        "Other Quantity Available", digits="Product Unit of Measure", compute="_compute_qty_at_date"
    )

    def _compute_qty_at_date(self):
        super(SaleOrderLine, self)._compute_qty_at_date()
        self.other_qty_available = 0
        treated = self.env["sale.order.line"]
        for line in self:
            if not line.display_qty_widget:
                continue
            line.vendor_qty_available = line.product_id.vendor_qty_available
            treated |= line
        remaining = self - treated
        remaining.vendor_qty_available = False
