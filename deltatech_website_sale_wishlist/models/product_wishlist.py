# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context

_logger = logging.getLogger(__name__)


class ProductWishlist(models.Model):
    _inherit = "product.wishlist"

    qty_available = fields.Float(
        "Quantity On Hand",
        compute="_compute_quantities",
        search="_search_qty_available",
        compute_sudo=False,
        digits="Product Unit of Measure",
    )

    def _compute_quantities(self):
        for item in self:
            item.qty_available = item.product_id.qty_available

    def _search_qty_available(self, operator, value):
        domain = [("qty_available", operator, value)]
        products = self.env["product.product"]._search(domain)
        return [("product_id", "in", products)]

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
