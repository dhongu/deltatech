# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class PropertyBuilding(models.Model):
    _inherit = "property.building"
    # _inherits = {'service.equipment': 'service_equipment_id'}

    tenant_id = fields.Many2one("res.partner", string="Tenant")
    agreement_id = fields.Many2one("service.agreement", string="Agreement")

    service_equipment_id = fields.Many2one("service.equipment", ondelete="restrict")

    @api.model_create_multi
    def create(self, vals_list):
        buildings = super(PropertyBuilding, self).create(vals_list)
        for building in buildings:
            service_equipment_id = self.env["service.equipment"].create(
                {
                    "name": building.name,
                    "base_equipment_id": building.base_equipment_id.id,
                    "internal_type": "building",
                    # 'type_id': asta trebuie determinat de undeva
                }
            )
            building.write({"service_equipment_id": service_equipment_id.id})
        return buildings
