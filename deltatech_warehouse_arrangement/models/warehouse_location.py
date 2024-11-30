# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import _, fields, models


def get_location_type(model):
    if model == "warehouse.location.rack":
        return _("Rack: ")
    if model == "warehouse.location.section":
        return _("Section: ")
    if model == "warehouse.location.shelf":
        return _("Shelf: ")
    if model == "warehouse.location.zone":
        return _("Zone: ")
    if model == "warehouse.location.storehouse":
        return _("Storehouse: ")
    return ""


class WarehouseLocationStorehouse(models.Model):
    _name = "warehouse.location.storehouse"
    _description = "Warehouse Storehouse"
    _order = "sequence, name"

    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")
    location_id = fields.Many2one("stock.location", string="Warehouse")
    full_name = fields.Char(compute="_compute_full_name")

    def _compute_full_name(self):
        for rec in self:
            rec.full_name = rec.location_id.name or "" + "/" + rec.name

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.name} ({rec.full_name})"
            result.append((rec.id, name))
        return result


class WarehouseLocationZone(models.Model):
    _name = "warehouse.location.zone"
    _description = "Warehouse Zone"
    _order = "sequence, name"

    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")
    storehouse_id = fields.Many2one("warehouse.location.storehouse", string="Storehouse")
    full_name = fields.Char(compute="_compute_full_name")

    def _compute_full_name(self):
        for rec in self:
            rec.full_name = (
                get_location_type("warehouse.location.storehouse")
                + rec.storehouse_id.name
                + "/"
                + get_location_type("warehouse.location.zone")
                + rec.name
            )

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.name} ({rec.full_name})"
            result.append((rec.id, name))
        return result


class WarehouseLocationShelf(models.Model):
    _name = "warehouse.location.shelf"
    _description = "Warehouse Shelf"
    _order = "sequence, name"

    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")
    zone_id = fields.Many2one("warehouse.location.zone", string="Zone")
    full_name = fields.Char(compute="_compute_full_name")

    def _compute_full_name(self):
        for rec in self:
            rec.full_name = (
                get_location_type("warehouse.location.storehouse")
                + rec.zone_id.storehouse_id.name
                + "/"
                + get_location_type("warehouse.location.zone")
                + rec.zone_id.name
                + "/"
                + get_location_type("warehouse.location.shelf")
                + rec.name
            )

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.name} ({rec.full_name})"
            result.append((rec.id, name))
        return result


class WarehouseLocationSection(models.Model):
    _name = "warehouse.location.section"
    _description = "Warehouse Section"
    _order = "sequence, name"

    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")
    shelf_id = fields.Many2one("warehouse.location.shelf", string="Shelf")
    full_name = fields.Char(compute="_compute_full_name")

    def _compute_full_name(self):
        for rec in self:
            rec.full_name = (
                get_location_type("warehouse.location.storehouse")
                + rec.shelf_id.zone_id.storehouse_id.name
                + "/"
                + get_location_type("warehouse.location.zone")
                + rec.shelf_id.zone_id.name
                + "/"
                + get_location_type("warehouse.location.shelf")
                + rec.shelf_id.name
                + "/"
                + get_location_type("warehouse.location.section")
                + rec.name
            )

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.name} ({rec.full_name})"
            result.append((rec.id, name))
        return result


class WarehouseLocationRack(models.Model):
    _name = "warehouse.location.rack"
    _description = "Warehouse Rack"
    _order = "sequence, name"

    sequence = fields.Integer(string="Sequence")
    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")
    section_id = fields.Many2one("warehouse.location.section", string="Section")
    full_name = fields.Char(compute="_compute_full_name")
    barcode = fields.Char()

    def _compute_full_name(self):
        for rec in self:
            rec.full_name = (
                get_location_type("warehouse.location.storehouse")
                + rec.section_id.shelf_id.zone_id.storehouse_id.name
                + "/"
                + get_location_type("warehouse.location.zone")
                + rec.section_id.shelf_id.zone_id.name
                + "/"
                + get_location_type("warehouse.location.shelf")
                + rec.section_id.shelf_id.name
                + "/"
                + get_location_type("warehouse.location.section")
                + rec.section_id.name
                + "/"
                + get_location_type("warehouse.location.rack")
                + rec.name
            )

    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.name} ({rec.full_name})"
            result.append((rec.id, name))
        return result
