# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ServiceMeter(models.Model):
    _inherit = "service.meter"

    equipment_id = fields.Many2one(
        "service.equipment", string="Apartment", required=True, ondelete="cascade", index=True
    )


class ServiceMeterReading(models.Model):
    _inherit = "service.meter.reading"

    equipment_id = fields.Many2one("service.equipment", string="Apartment", required=True, ondelete="restrict")
