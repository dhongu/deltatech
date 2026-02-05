# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("order_line")
    def onchange_order_line(self):
        pallets = self.recompute_pallet_lines(delete_if_under=True)
        if pallets:
            for line in self.order_line:
                pallet = pallets.pop(line.product_id.id, False)
                if pallet:
                    # line.product_uom_qty = max(pallet["product_uom_qty"], line.product_uom_qty)
                    line.product_uom_qty = pallet["product_uom_qty"]

        for product_id in pallets:
            if pallets and pallets[product_id]["product_uom_qty"]:
                order_line = self.order_line.new(pallets[product_id])
                order_line._onchange_product_id_warning()
                # order_line.product_uom_change()

    def recompute_pallet_lines(self, delete_if_under=False):
        pallets = {}
        for line in self.order_line:
            if line.product_id.pallet_product_id and line.product_id.pallet_qty_min:
                # search for lines with same pallet
                product = line.product_id.pallet_product_id
                prod_with_pallet_lines = self.order_line.filtered(
                    lambda p, product_id=product.id: p.product_id.pallet_product_id.id == product_id
                )

                # compute sum for all lines with pallets
                qty = 0
                for prod_with_pallet_line in prod_with_pallet_lines:
                    qty += prod_with_pallet_line.compute_pallet_number(delete_if_under)

                pallets[line.product_id.pallet_product_id.id] = {
                    "product_uom_qty": qty,
                    "product_id": line.product_id.pallet_product_id.id,
                    "state": "draft",
                    "order_id": self.id,
                }
        return pallets


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def compute_pallet_number(self, delete_if_under=False):
        self.ensure_one()
        res = 0
        if self.product_id.pallet_product_id and self.product_id.pallet_qty_min:
            if self.product_id.pallet_qty_min > self.product_uom_qty:
                if delete_if_under:
                    res = 0
                else:
                    res = 1
            else:
                pallets = self.product_uom_qty / self.product_id.pallet_qty_min
                if delete_if_under:
                    res = round(pallets - 0.49)  # round down
                else:
                    res = round(pallets + 0.49)  # round up
        return res
