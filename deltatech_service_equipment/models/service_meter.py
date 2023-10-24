# ©  2015-2022 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.exceptions import UserError


class ServiceMeterCategory(models.Model):
    _inherit = "service.meter.category"

    bill_uom_id = fields.Many2one("uom.uom", string="Billing Unit of Measure")


class ServiceMeterReading(models.Model):
    _inherit = "service.meter.reading"

    address_id = fields.Many2one(
        "res.partner",
        string="Location",
        related="equipment_id.address_id",
        readonly=True,
        help="The address where the equipment is located",
    )

    consumption_id = fields.Many2one("service.consumption", string="Consumption", readonly=True)

    def unlink(self):
        meters = self.env["service.meter"]
        for reading in self:
            if reading.consumption_id:
                raise UserError(_("Meter reading recorder in consumption prepared for billing."))
            meters |= reading.meter_id

        res = super().unlink()

        meters.recheck_value()

        return res
