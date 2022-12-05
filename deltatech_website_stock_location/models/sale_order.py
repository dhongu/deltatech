# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        if self.website_id:
            if not self.website_id.warehouse_id:
                self = self.with_context(all_warehouses=True)
            if not self.website_id.location_id:
                self = self.with_context(all_locations=True)
        values = super(SaleOrder, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)
        return values
