# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    loc_storehouse_id = fields.Many2one("warehouse.location.storehouse", string="Storehouse")
    loc_zone_id = fields.Many2one("warehouse.location.zone", string="Zone")
    loc_shelf_id = fields.Many2one("warehouse.location.shelf", string="Shelf")
    loc_section_id = fields.Many2one("warehouse.location.section", string="Section")
    loc_rack_id = fields.Many2one("warehouse.location.rack", string="Rack")

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
