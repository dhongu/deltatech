# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    loc_storehouse_id = fields.Many2one(
        "warehouse.location.storehouse", related="product_id.loc_storehouse_id", store=True
    )
    loc_zone_id = fields.Many2one("warehouse.location.zone", related="lot_id.loc_zone_id", store=True)
    loc_shelf_id = fields.Many2one("warehouse.location.shelf", related="lot_id.loc_shelf_id", store=True)
    loc_section_id = fields.Many2one("warehouse.location.section", related="lot_id.loc_section_id", store=True)
    loc_rack_id = fields.Many2one("warehouse.location.rack", related="lot_id.loc_rack_id", store=True)
