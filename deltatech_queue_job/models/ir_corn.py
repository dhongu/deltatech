# ©  2022 Deltatech
# See README.rst file on addons root folder for license details


import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import fields, models

_logger = logging.getLogger(__name__)


class BadVersion(Exception):
    pass


class BadModuleState(Exception):
    pass


class IrCron(models.Model):
    _inherit = "ir.cron"

    def _trigger(self, at=None):
        if at is None:
            at = fields.Datetime.now()
        assert isinstance(at, datetime)
        try:
            if self.nextcall > at + relativedelta(minutes=10):
                self.write({"nextcall": at})
        except Exception as e:
            _logger.error(str(e))
