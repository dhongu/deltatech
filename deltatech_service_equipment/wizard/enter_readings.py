# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models


class ServiceEnterReading(models.TransientModel):
    _name = "service.enter.reading"
    _description = "Enter Meter Readings"

    date = fields.Date(string="Date", index=True, required=True, default=fields.Date.today())

    read_by = fields.Many2one("res.partner", string="Read by", domain=[("is_company", "=", False)])
    note = fields.Text(string="Notes")
    items = fields.One2many("service.enter.reading.item", "enter_reading_id")
    error = fields.Text(compute="_compute_error")

    @api.depends("items.counter_value")
    def _compute_error(self):
        self.error = ""
        for item in self.items:
            domain = [("date", ">", self.date), ("meter_id", "=", item.meter_id.id)]
            future_readings = self.env["service.meter.reading"].search(domain)
            if future_readings:
                self.error += _("The counter %s has readings in the future!!!") % (item.meter_id.name)
                self.error += "<br/>\r\n"
            if item.counter_value <= item.meter_id.total_counter_value and item.meter_id.total_counter_value > 0:
                self.error += _("The counter %s value must be greater than %s.<br/>") % (
                    item.meter_id.name,
                    item.meter_id.total_counter_value,
                )

    @api.model
    def default_get(self, fields_list):
        defaults = super(ServiceEnterReading, self).default_get(fields_list)

        active_ids = self.env.context.get("active_ids", False)
        domain = [("equipment_id", "in", active_ids)]
        meters = self.env["service.meter"].search(domain)
        defaults["items"] = []
        for meter in meters:
            if meter.type == "counter":
                values = {
                    "meter_id": meter.id,
                    "equipment_id": meter.equipment_id.id,
                    "counter_value": meter.estimated_value,
                    "prev_value": meter.total_counter_value,
                }
                defaults["items"] += [
                    (
                        0,
                        0,
                        values,
                    )
                ]

        return defaults

    @api.onchange("date")
    def onchange_date(self):

        for item in self.items:
            meter = item.meter_id

            if meter.type == "counter":
                meter = meter.with_context({"date": self.date})
                item.counter_value = meter.estimated_value

    def do_enter(self):
        equipments = self.env["service.equipment"]
        for enter_reading in self:
            for item in enter_reading.items:
                self.env["service.meter.reading"].create(
                    {
                        "meter_id": item.meter_id.id,
                        "equipment_id": item.meter_id.equipment_id.id,
                        "date": enter_reading.date,
                        "read_by": enter_reading.read_by.id,
                        "note": enter_reading.note,
                        "counter_value": item.counter_value,
                        "estimated": item.estimated,
                        "previous_counter_value": item.prev_value,
                    }
                )
                equipments |= item.equipment_id
        equipments.update_meter_status()


class ServiceEnterReadingItem(models.TransientModel):
    _name = "service.enter.reading.item"
    _description = "Enter Meter Reading Item"

    enter_reading_id = fields.Many2one("service.enter.reading", string="Enter Reading")
    meter_id = fields.Many2one("service.meter", string="Meter")
    equipment_id = fields.Many2one("service.equipment", string="Equipment")
    counter_value = fields.Float(string="Counter Value", digits="Meter Value", required=True)
    prev_value = fields.Float(string="Previous Value", digits="Meter Value", required=False)
    estimated = fields.Boolean(string="Estimated")
