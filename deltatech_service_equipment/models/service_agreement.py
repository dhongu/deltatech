# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models


class ServiceAgreement(models.Model):
    _inherit = "service.agreement"

    def service_equipment(self):
        equipments = self.env["service.equipment"]

        for item in self.agreement_line:
            if item.equipment_id:
                equipments = equipments + item.equipment_id

        res = []
        for equipment in equipments:
            res.append(equipment.id)

        return {
            "domain": "[('id','in', [" + ",".join(map(str, res)) + "])]",
            "name": _("Services Equipment"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "service.equipment",
            "view_id": False,
            "type": "ir.actions.act_window",
        }


class ServiceAgreementLine(models.Model):
    _inherit = "service.agreement.line"

    equipment_id = fields.Many2one("service.equipment", string="Equipment", index=True)
    meter_id = fields.Many2one("service.meter", string="Meter")

    # de adaugat constringerea ca unitatea de masura de la linie sa fi la fel ca si cea de la meter

    @api.onchange("equipment_id")
    def onchange_equipment_id(self):
        if self.equipment_id:
            self.meter_id = self.equipment_id.meter_ids[0]

    @api.onchange("meter_id")
    def onchange_meter_id(self):
        if self.meter_id:
            self.equipment_id = self.meter_id.equipment_id
            # self.uom_id = self.meter_id.uom_id

    @api.model
    def after_create_consumption(self, consumption):
        # readings = self.env['service.meter.reading']
        # la data citirii echipamentul functiona in baza contractului???\\
        # daca echipamentul a fost inlocuit de unul de rezeva ?

        self.ensure_one()
        res = [consumption.id]  # trebuie musai fa folosesc super ???
        if self.equipment_id:

            meter = self.meter_id
            equipment = self.equipment_id
            de_la_data = consumption.agreement_id.date_agreement  # si eventual de pus data de instalare
            if meter:

                # se citesc inregistrarile la care a fost generat cosnumul
                readings = meter.meter_reading_ids.filtered(lambda r: r.consumption_id)
                if readings:
                    de_la_data = max([readings[0].date, de_la_data])

                # se selecteaza citirile care nu sunt facturate
                # se selecteaza citirile care sunt anterioare sfarsitului de perioada,
                # e pozibil ca sa mai fie citiri in perioada anterioara nefacturate

                # sa fie dupa data de instalare si dupa ultima citire facturata

                readings = meter.meter_reading_ids.filtered(
                    lambda r: not r.consumption_id and consumption.period_id.date_end >= r.date >= de_la_data
                )

                quantity = 0

                for reading in readings:
                    from_uom = reading.meter_id.uom_id
                    to_uom = consumption.agreement_line_id.uom_id

                    amount = reading.difference / from_uom.factor
                    if to_uom:
                        amount = amount * to_uom.factor

                    quantity += amount

                name = self.equipment_id.display_name + "\n"

                if readings:
                    first_reading = readings[-1]
                    last_reading = readings[0]
                    name += _("Old index: %s, New index:%s") % (
                        first_reading.previous_counter_value,
                        last_reading.counter_value,
                    )

                    readings.write({"consumption_id": consumption.id})

                consumption.write({"quantity": quantity, "name": name, "equipment_id": equipment.id})

            else:  # echipament fara contor
                consumption.write({"name": self.equipment_id.display_name, "equipment_id": equipment.id})
        return res


class ServiceConsumption(models.Model):
    _inherit = "service.consumption"

    equipment_id = fields.Many2one("service.equipment", string="Equipment", index=True)

    _sql_constraints = [
        (
            "agreement_line_period_uniq",
            "unique(period_id,agreement_line_id,equipment_id)",
            "Agreement line in period already exist!",
        ),
    ]
