# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def _gather(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False):
        quants = super(StockQuant, self)._gather(product_id, location_id, lot_id, package_id, owner_id, strict)
        if not lot_id:
            # trebuie sa pastrez in lista doar loturile noi
            pass
        return quants
