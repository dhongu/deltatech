# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("order_line")
    def onchange_order_line(self):
        pallets = {}
        for line in self.order_line:
            if (
                line.product_id.pallet_product_id
                and line.product_id.pallet_qty_min
                and line.product_uom_qty >= line.product_id.pallet_qty_min
            ):
                pallet = pallets.get(line.product_id, False)
                if pallet:
                    qty = pallet["product_uom_qty"]
                else:
                    qty = 0
                qty = qty + line.product_uom_qty / line.product_id.pallet_qty_min
                qty = line.product_id.pallet_product_id.uom_id._compute_quantity(
                    qty, line.product_id.pallet_product_id.uom_id
                )
                pallets[line.product_id.pallet_product_id.id] = {
                    "product_uom_qty": qty,
                    "product_id": line.product_id.pallet_product_id.id,
                    "state": "draft",
                    "order_id": self.id,
                }

        if pallets:
            for line in self.order_line:
                pallet = pallets.pop(line.product_id.id, False)
                if pallet:
                    line.product_uom_qty = max(pallet["product_uom_qty"], line.product_uom_qty)

        for product_id in pallets:
            order_line = self.order_line.new(pallets[product_id])
            order_line.product_id_change()
            order_line.product_uom_change()
