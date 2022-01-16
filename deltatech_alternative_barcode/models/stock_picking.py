# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def on_barcode_scanned(self, barcode):
        domain = [("code", "=", barcode)]
        alternative = self.env["product.alternative"].search(domain, limit=1)
        if alternative:
            product = alternative.product_tmpl_id.product_variant_id
            if product:
                if self._check_product(product):
                    return
        return super(StockPicking, self).on_barcode_scanned(barcode)
