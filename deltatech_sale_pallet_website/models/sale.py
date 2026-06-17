# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _verify_cart_after_update(self):
        # În Odoo 19 API-ul website_sale a fost refactorizat: `_cart_update`
        # nu mai există. Hook-ul `_verify_cart_after_update` este apelat după
        # `_cart_add` și `_cart_update_line_quantity`, deci e locul potrivit
        # pentru recalcul liniilor de palet.
        res = super()._verify_cart_after_update()
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
