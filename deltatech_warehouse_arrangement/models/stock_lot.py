# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.tools import float_is_zero


class StockLot(models.Model):
    _inherit = "stock.lot"

    loc_storehouse_id = fields.Many2one("warehouse.location.storehouse", string="Storehouse")
    loc_zone_id = fields.Many2one("warehouse.location.zone", string="Zone")
    loc_shelf_id = fields.Many2one("warehouse.location.shelf", string="Shelf Loc")
    loc_section_id = fields.Many2one("warehouse.location.section", string="Section Loc")
    loc_rack_id = fields.Many2one("warehouse.location.rack", string="Rack Loc")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            product_id = self.env["product.product"].browse(vals["product_id"])
            vals["loc_storehouse_id"] = product_id.loc_storehouse_id.id
            vals["loc_zone_id"] = product_id.loc_zone_id.id
            vals["loc_shelf_id"] = product_id.loc_shelf_id.id
            vals["loc_section_id"] = product_id.loc_section_id.id
            vals["loc_rack_id"] = product_id.loc_rack_id.id
        return super().create(vals_list)

    def check_if_depleted(self, location_id):
        """
        Check if quantity becomes 0 on the stock location
        and delete locations if 0
        :param location_id: location in which to check
        :return:
        """
        for lot in self:
            if lot.loc_storehouse_id.location_id:
                stock_location_id = location_id
                children_location = (
                    self.env["stock.location"]
                    .with_context(active_test=False)
                    .search([("id", "child_of", stock_location_id.ids)])
                )
                internal_children_locations = children_location.filtered(lambda l: l.usage == "internal")
                quants = lot.quant_ids.filtered(lambda q: q.location_id in internal_children_locations)
                product_qty = sum(quants.mapped("quantity"))
                if float_is_zero(product_qty, precision_rounding=lot.product_id.uom_id.rounding):
                    lot.write(
                        {
                            "loc_storehouse_id": False,
                            "loc_zone_id": False,
                            "loc_shelf_id": False,
                            "loc_section_id": False,
                            "loc_rack_id": False,
                        }
                    )
