# ©  2015-2021 Terrabit Solutions
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import models


class ServiceEquiOperation(models.TransientModel):
    _inherit = "service.equi.operation"

    def do_operation(self):
        counters = ""
        # se vor lua din wizard
        # equipment = self.equipment_id
        # if equipment.meter_ids:
        #     for meter in equipment.meter_ids:
        #         counters += str(meter.uom_id)+': '+str(meter.total_counter_value)+'\r\n'
        for reading in self.items:
            counters += str(reading.meter_id.uom_id.name) + ": " + str(reading.counter_value) + "\r\n"

        if self.state == "ins":
            emplacement = self.emplacement or ""
            values = {
                "name": "Instalare",
                "equipment_id": self.equipment_id.id,
                "description": "Instalare echipament la "
                + self.partner_id.name
                + ", punct de lucru "
                + self.address_id.name
                + ", amplasament "
                + emplacement
                + ".\r\nContori:"
                + counters,
            }
            self.env["common.history"].create(values)
        if self.state == "rem":
            emplacement = self.equipment_id.emplacement or ""
            values = {
                "name": "Dezinstalare",
                "equipment_id": self.equipment_id.id,
                # 'description': 'Dezinstalare echipament.\r\nlContori:'+counters
                "description": "Dezinstalare echipament de la "
                + self.equipment_id.partner_id.name
                + ", punct de lucru "
                + self.equipment_id.address_id.name
                + ", amplasament "
                + emplacement
                + ".\r\nContori:"
                + counters,
            }
            self.env["common.history"].create(values)
        return super(ServiceEquiOperation, self).do_operation()
