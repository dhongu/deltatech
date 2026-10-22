# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class SaleMarginReport(models.Model):
    _inherit = "sale.margin.report"

    manufacturer_id = fields.Many2one("res.partner", string="Manufacturer", readonly=True)

    def _select(self):
        return super()._select() + ", manufacturer_id"

    def _sub_select(self):
        return super()._sub_select() + ", t.manufacturer_id"

    def _group_by(self):
        return super()._group_by() + ", t.manufacturer_id"
