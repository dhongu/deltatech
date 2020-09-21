# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


import logging
import math
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import RedirectWarning, Warning, except_orm
from odoo.tools import float_compare

import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class service_meter(models.Model):
    _inherit = "service.meter"

    equipment_id = fields.Many2one(
        "service.equipment", string="Apartment", required=True, ondelete="cascade", index=True
    )


class service_meter_reading(models.Model):
    _inherit = "service.meter.reading"

    equipment_id = fields.Many2one("service.equipment", string="Apartment", required=True, ondelete="restrict")
