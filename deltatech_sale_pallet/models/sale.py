# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("order_line")
    def onchange_order_line(self):
        pallets = self.recompute_pallet_lines()
        if pallets:
            for line in self.order_line:
                pallet = pallets.pop(line.product_id.id, False)
                if pallet:
                    # line.product_uom_qty = max(pallet["product_uom_qty"], line.product_uom_qty)
                    line.product_uom_qty = pallet["product_uom_qty"]

        for product_id in pallets:
            order_line = self.order_line.new(pallets[product_id])
            order_line.product_id_change()
            order_line.product_uom_change()

    def recompute_pallet_lines(self):
        pallets = {}
        for line in self.order_line:
            if (
                line.product_id.pallet_product_id
                and line.product_id.pallet_qty_min
                and line.product_uom_qty >= line.product_id.pallet_qty_min
            ):
                # search for lines with same pallet
                prod_with_pallet_lines = self.order_line.filtered(
                    lambda p: p.product_id.pallet_product_id == line.product_id.pallet_product_id
                )

                # compute sum for all lines with pallets
                qty = 0
                for prod_with_pallet_line in prod_with_pallet_lines:
                    qty += prod_with_pallet_line.compute_pallet_number()

                pallets[line.product_id.pallet_product_id.id] = {
                    "product_uom_qty": qty,
                    "product_id": line.product_id.pallet_product_id.id,
                    "state": "draft",
                    "order_id": self.id,
                }
        return pallets


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def compute_pallet_number(self):
        self.ensure_one()
        if self.product_id.pallet_product_id and self.product_id.pallet_qty_min:
            if self.product_id.pallet_qty_min > self.product_uom_qty:
                return 1
            else:
                pallets = self.product_uom_qty / self.product_id.pallet_qty_min
                return round(pallets + 0.49)  # round up
