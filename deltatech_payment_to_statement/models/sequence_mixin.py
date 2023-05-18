# Copyright (C) 2015-2023 Deltatech
# Copyright (C) 2022 NextERP Romania
# License OPL-1.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.tools.safe_eval import safe_eval


class SequenceMixin(models.AbstractModel):
    _inherit = "sequence.mixin"

    def _constrains_date_sequence(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        override = safe_eval(get_param("override_sequence_date_constraint", "False"))
        if override:
            return True
        else:
            return super()._constrains_date_sequence()
