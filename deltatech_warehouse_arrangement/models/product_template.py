# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    loc_storehouse_id = fields.Many2one("warehouse.location.storehouse", string="Storehouse")
    loc_zone_id = fields.Many2one("warehouse.location.zone", string="Zone")
    loc_shelf_id = fields.Many2one("warehouse.location.shelf", string="Shelf Loc")
    loc_section_id = fields.Many2one("warehouse.location.section", string="Section Loc")
    loc_rack_id = fields.Many2one("warehouse.location.rack", string="Rack Loc")
