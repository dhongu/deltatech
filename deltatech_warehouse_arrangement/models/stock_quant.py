# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    loc_storehouse_id = fields.Many2one(
        "warehouse.location.storehouse", related="product_id.loc_storehouse_id", store=True
    )
    loc_zone_id = fields.Many2one("warehouse.location.zone", related="product_id.loc_zone_id", store=True)
    loc_shelf_id = fields.Many2one("warehouse.location.shelf", related="product_id.loc_shelf_id", store=True)
    loc_section_id = fields.Many2one("warehouse.location.section", related="product_id.loc_section_id", store=True)
    loc_rack_id = fields.Many2one("warehouse.location.rack", related="product_id.loc_rack_id", store=True)

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         product_id = self.env["product.product"].browse(vals["product_id"])
    #         vals["loc_storehouse_id"] = product_id.loc_storehouse_id.id
    #         vals["loc_zone_id"] = product_id.loc_zone_id.id
    #         vals["loc_shelf_id"] = product_id.loc_shelf_id.id
    #         vals["loc_section_id"] = product_id.loc_section_id.id
    #         vals["loc_rack_id"] = product_id.loc_rack_id.id
    #     return super().create(vals_list)
