# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


import math
from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import RedirectWarning, Warning, except_orm
from odoo.tools import float_compare

import odoo.addons.decimal_precision as dp


class service_equipment(models.Model):
    _description = "Apartment"
    _inherit = "service.equipment"

    group_id = fields.Many2one("service.agreement.group", string="Building")

    @api.multi
    def _update_labels(self):
        translations = self.env["ir.translation"].search(
            [("module", "like", "service"), ("source", "like", "Equipment")]
        )
        translations.unlink()
        translations = self.env["ir.translation"].search(
            [("module", "like", "service"), ("source", "like", "Service Group")]
        )
        translations.unlink()


class service_equipment_category(models.Model):
    _inherit = "service.equipment.category"
    _description = "Apartment Category"
    name = fields.Char(string="Category", translate=True)


class service_equipment_type(models.Model):
    _inherit = "service.equipment.type"
    _description = "Apartment Type"
