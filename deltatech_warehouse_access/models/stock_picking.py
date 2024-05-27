# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging

from odoo import _, models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        for picking in self:
            warehouse = picking.picking_type_id.warehouse_id
            if self.env.user not in warehouse.user_ids and warehouse.user_ids:
                msg = _("The %(user_name)s user don’t have access to the %(warehouse_name)s warehouse") % {
                    "user_name": self.env.user.name,
                    "warehouse_name": warehouse.name,
                }
                raise AccessError(msg)
        return super().button_validate()
