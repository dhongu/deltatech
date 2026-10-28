# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.tools import SQL


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    manufacturer_id = fields.Many2one("res.partner", string="Manufacturer", readonly=True)

    def _select(self):
        return SQL("%s, t.manufacturer_id", super()._select())

    def _group_by(self):
        return SQL("%s, t.manufacturer_id", super()._group_by())
