# ©  2015-2021 Terrabit Solutions
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details


from odoo import models


class ServiceEquiAgreement(models.TransientModel):
    _inherit = "service.equi.agreement"

    def do_agreement(self):
        res = super(ServiceEquiAgreement, self).do_agreement()
        equipment = self.equipment_id
        counters = ""
        if equipment.meter_ids:
            for meter in equipment.meter_ids:
                counters += str(meter.uom_id.name) + ": " + str(meter.total_counter_value) + "\r\n"
        emplacement = self.equipment_id.emplacement or ""
        values = {
            "name": "Adaugare la contract",
            "equipment_id": self.equipment_id.id,
            "agreement_id": self.agreement_id.id,
            # 'description': 'Adaugare la contract.\r\nContori:' + counters
            "description": "Adaugare la contract nr "
            + self.agreement_id.name
            + ", Partener "
            + self.equipment_id.partner_id.name
            + ", punct de lucru "
            + self.equipment_id.address_id.name
            + ", amplasament "
            + emplacement
            + ".\r\nContori:"
            + counters,
        }
        self.env["common.history"].create(values)
        return res
