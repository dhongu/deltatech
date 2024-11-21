# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _action_done(self):
        res = super()._action_done()
        for ml in self:
            # if a lot/serial enters the master location
            try:
                if (
                    ml.lot_id
                    and ml.product_id.loc_storehouse_id
                    and ml.product_id.loc_storehouse_id.location_id == ml.location_dest_id
                ):
                    ml.lot_id.write(
                        {
                            "loc_storehouse_id": ml.product_id.loc_storehouse_id.id,
                            "loc_zone_id": ml.product_id.loc_zone_id.id,
                            "loc_shelf_id": ml.product_id.loc_shelf_id.id,
                            "loc_section_id": ml.product_id.loc_section_id.id,
                            "loc_rack_id": ml.product_id.loc_rack_id.id,
                        }
                    )
                # if a lot/serial leaves the master location and the quantity in that location remains 0
                if (
                    ml.lot_id
                    and ml.lot_id.loc_storehouse_id
                    and ml.lot_id.loc_storehouse_id.location_id == ml.location_id
                ):
                    ml.lot_id.check_if_depleted(ml.location_id)
            except Exception as e:
                _logger.info(e)
        return res
