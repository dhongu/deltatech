# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        res = super()._cart_update(product_id=product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty, **kwargs)
        pallets = self.recompute_pallet_lines(delete_if_under=True)

        if pallets:
            for line in self.order_line:
                pallet = pallets.pop(line.product_id.id, False)
                if pallet:
                    product_uom_qty = pallet["product_uom_qty"]
                    if product_uom_qty:
                        line.write({"product_uom_qty": product_uom_qty})
                    else:
                        line.unlink()

        for product_id in pallets:
            if pallets[product_id]["product_uom_qty"]:
                self.env["sale.order.line"].create(pallets[product_id])

        return res
