# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models
from odoo.http import request


class Website(models.Model):
    _inherit = "website"

    def sale_get_order(self, *args, **kwargs):
        so = super().sale_get_order(*args, **kwargs)
        acquirer_id = request.context.get("acquirer_id")
        if acquirer_id:
            so = so.with_context(force_acquirer_id=acquirer_id)
        return so
