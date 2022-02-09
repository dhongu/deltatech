# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details


from datetime import timedelta

from odoo import _, api, fields, models


class ServiceAgreementType(models.Model):
    _inherit = "service.agreement.type"

    permits_pickings = fields.Boolean("Allows non-billable deliveries", default=False)
    readings_required = fields.Boolean("Requires readings for billing", default=False)


class ServiceAgreement(models.Model):
    _inherit = "service.agreement"

    equipment_count = fields.Integer(compute="_compute_equipment_count")
    common_history_ids = fields.One2many("service.history", "agreement_id", string="Agreement History")
    meter_reading_status = fields.Boolean(default=False, string="Readings done", tracking=True)

    @api.depends("agreement_line")
    def _compute_equipment_count(self):
        for agreement in self:
            equipments = self.env["service.equipment"]

            for item in agreement.agreement_line:
                if item.equipment_id:
                    equipments |= item.equipment_id

            agreement.equipment_count = len(equipments)

    def get_agreements_auto_billing(self):
        agreements = super(ServiceAgreement, self).get_agreements_auto_billing()
        for agreement in agreements:
            # check if readings done
            if not agreement.meter_reading_status:
                agreements = agreements - agreement
        return agreements

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

    def do_agreement(self):
        pass

    def common_history_button(self):
        return {
            "domain": [("id", "in", self.common_history_ids.ids)],
            "name": "History",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "service.history",
            "view_id": False,
            "type": "ir.actions.act_window",
        }

    @api.onchange("meter_reading_status")
    def check_reading_status(self):
        # self.error = ''
        if self.meter_reading_status:
            date_today = fields.Date.context_today(self)
            limit_date = date_today - timedelta(days=7)
            self.ensure_one()
            equipments = self.env["service.equipment"]
            for item in self.agreement_line:
                if item.equipment_id:
                    equipments |= item.equipment_id
            for equipment in equipments:
                if not equipment.meter_ids:
                    continue
                equipment._compute_readings_status()
                if equipment.last_reading < limit_date:
                    self.meter_reading_status = False
                    message = "Device {}/{} (serial:{}): no reads older than 7 days ".format(
                        equipment.name,
                        equipment.address_id.name,
                        equipment.serial_id.name,
                    )
                    return {
                        "warning": {"title": "Warning", "message": message, "type": "notification"},
                    }
                    # self.error += "Echipament %s/%s (serial: %s): nu exista citiri mai noi de 7 zile | " %
                    # (equipment.name, equipment.address_id.name, equipment.serial_id.name)


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
        self.ensure_one()
        super(ServiceAgreementLine, self).after_create_consumption(consumption)
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
