# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context

_logger = logging.getLogger(__name__)


class ProductWishlist(models.Model):
    _inherit = "product.wishlist"

    def action_launch_replenishment(self):

        warehouse = self.env.user._get_default_warehouse_id()
        for line in self:
            uom_reference = line.product_id.uom_id
            try:
                self.env["procurement.group"].with_context(clean_context(self.env.context)).run(
                    [
                        self.env["procurement.group"].Procurement(
                            line.product_id,
                            1,
                            uom_reference,
                            warehouse.lot_stock_id,  # Location
                            _("Required for wishlist"),  # Name
                            _("wishlist"),  # Origin
                            warehouse.company_id,  # Company
                            line._prepare_run_values(),  # Values
                        )
                    ]
                )
            except UserError as error:
                raise UserError(error)

    def _prepare_run_values(self):
        replenishment = self.env["procurement.group"].create(
            {
                "partner_id": self.product_id.with_company(self.env.user.company_id).responsible_id.partner_id.id,
            }
        )

        values = {
            "warehouse_id": self.env.user._get_default_warehouse_id(),
            "group_id": replenishment,
        }
        return values
