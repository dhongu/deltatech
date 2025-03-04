# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestProperty(TransactionCase):
    def test_property_land(self):
        form_land = Form(self.env["property.land"])
        form_land.name = "Test"
        form_land.save()

    def test_property_building(self):
        form_building = Form(self.env["property.building"])
        form_building.name = "Test"
        form_building.save()

    def test_property_room(self):
        building = self.env["property.building"].create({"name": "Test"})
        form_room = Form(self.env["property.room"])
        form_room.building_id = building
        form_room.save()
