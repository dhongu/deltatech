# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductChangeQuantity(models.TransientModel):
    _inherit = "stock.change.product.qty"

    location_id = fields.Many2one("stock.location", string="Location")

    @api.model
    def default_get(self, fields_list):
        defaults = super(ProductChangeQuantity, self).default_get(fields_list)
        warehouse = self.env["stock.warehouse"].search([("company_id", "=", self.env.company.id)], limit=1)
        defaults["location_id"] = warehouse.lot_stock_id.id
        return defaults

    def change_product_qty(self):
        """ Sandard se face ajustarea de quant"""

        inventory = self.env["stock.inventory"].create(
            {"product_ids": [(6, 0, [self.product_id.id])], "location_ids": [(6, 0, [self.location_id.id])]}
        )
        inventory.action_start()
        if len(inventory.line_ids) > 1:
            raise UserError(_("The inventory cannot be made from this place"))

        if not inventory.line_ids:
            self.env["stock.inventory.line"].create(
                {"inventory_id": inventory.id, "product_id": self.product_id.id, "location_id": self.location_id.id}
            )

        inventory.line_ids.product_qty = self.new_quantity

        res = inventory.action_validate()

        return res
