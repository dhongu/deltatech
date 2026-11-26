# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

from odoo import api, fields, models
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
        digits="Product Unit",
    )

    @api.depends("product_id", "product_id.qty_available")
    @api.depends_context(
        "lot_id",
        "owner_id",
        "package_id",
        "from_date",
        "to_date",
        "location",
        "warehouse_id",
        "allowed_company_ids",
    )
    def _compute_quantities(self):
        for item in self:
            item.qty_available = item.product_id.qty_available

    @api.depends("partner_id", "product_id")
    def _compute_display_name(self):
        for item in self:
            names = [item.partner_id.display_name, item.product_id.display_name]
            item.display_name = " - ".join(name for name in names if name)

    def _search_qty_available(self, operator, value):
        domain = [("qty_available", operator, value)]
        products = self.env["product.product"]._search(domain)
        return [("product_id", "in", products)]

    def action_launch_replenishment(self):
        warehouse = self.env.user._get_default_warehouse_id()
        for line in self:
            uom_reference = line.product_id.uom_id
            try:
                self.env["stock.rule"].with_context(**clean_context(self.env.context)).run(
                    [
                        self.env["stock.rule"].Procurement(
                            line.product_id,
                            1,
                            uom_reference,
                            warehouse.lot_stock_id,  # Location
                            self.env._("Required for wishlist"),  # Name
                            self.env._("wishlist"),  # Origin
                            warehouse.company_id,  # Company
                            line._prepare_run_values(),  # Values
                        )
                    ]
                )
            except UserError as error:
                raise UserError(error) from error

    def _prepare_run_values(self):
        # în Odoo 19 procurement.group a fost înlocuit de stock.reference
        reference = self.env["stock.reference"].create({"name": self.env._("Wishlist replenishment")})

        values = {
            "warehouse_id": self.env.user._get_default_warehouse_id(),
            "reference_ids": reference,
            "partner_id": self.product_id.with_company(self.env.company).responsible_id.partner_id.id,
        }
        return values
