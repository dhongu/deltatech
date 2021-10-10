# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models


class Base(models.AbstractModel):
    _inherit = "base"

    def with_delay(self, priority=None, eta=None, max_retries=None, description=None, channel=None, identity_key=None):

        return self
