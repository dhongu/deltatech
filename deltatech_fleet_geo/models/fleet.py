# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class FleetVehicleLocation(models.Model):
    _inherit = "fleet.vehicle.location"

    lat = fields.Float("Latitude", digits=(9, 6))
    lng = fields.Float("Longitude", digits=(9, 6))


class FleetLocation(models.Model):
    _inherit = "fleet.location"
    "Pozitia unei locatii si afisare pozitie pe Google Maps"

    lat = fields.Float("Latitude", digits=(9, 6))
    lng = fields.Float("Longitude", digits=(9, 6))
    radius = fields.Float("Radius", default=1.0)  # raza in km sau metri


class FleetRoute(models.Model):
    _inherit = "fleet.route"

    from_lat = fields.Float(related="from_loc_id.lat", digits=(9, 6), string="Latitude from")
    from_lng = fields.Float(related="from_loc_id.lng", digits=(9, 6), string="Longitude from")
    to_lat = fields.Float(related="to_loc_id.lat", digits=(9, 6), string="Latitude to")
    to_lng = fields.Float(related="to_loc_id.lng", digits=(9, 6), string="Longitude to")


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    def action_get_location(self):
        pass
