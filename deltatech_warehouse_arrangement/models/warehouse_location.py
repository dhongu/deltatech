# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import fields, models


class WarehouseLocationStorehouse(models.Model):
    _name = "warehouse.location.storehouse"
    _description = "Warehouse Storehouse"
    _order = "sequence, name"

    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse")


class WarehouseLocationZone(models.Model):
    _name = "warehouse.location.zone"
    _description = "Warehouse Zone"
    _order = "sequence, name"

    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")
    storehouse_id = fields.Many2one("warehouse.location.storehouse", string="Storehouse")


class WarehouseLocationShelf(models.Model):
    _name = "warehouse.location.shelf"
    _description = "Warehouse Shelf"
    _order = "sequence, name"

    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")
    zone_id = fields.Many2one("warehouse.location.zone", string="Zone")


class WarehouseLocationSection(models.Model):
    _name = "warehouse.location.section"
    _description = "Warehouse Section"
    _order = "sequence, name"

    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")
    shelf_id = fields.Many2one("warehouse.location.shelf", string="Shelf")


class WarehouseLocationRack(models.Model):
    _name = "warehouse.location.rack"
    _description = "Warehouse Rack"
    _order = "sequence, name"

    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")
    section_id = fields.Many2one("warehouse.location.section", string="Section")
    full_name = fields.Char(compute="_compute_full_name")

    def _compute_full_name(self):
        for rack in self:
            rack.full_name = (
                self.section_id.shelf_id.zone_id.storehouse_id.name
                + "/"
                + self.section_id.shelf_id.zone_id.name
                + "/"
                + self.section_id.shelf_id.name
                + "/"
                + self.section_id.name
                + "/"
                + self.name
            )
