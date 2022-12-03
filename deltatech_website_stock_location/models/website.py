# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    location_id = fields.Many2one("stock.location", string="Stock Location")

    def _get_warehouse_available(self):
        if not self.warehouse_id:
            self = self.with_context(all_warehouses=True)
        if not self.location_id:
            self = self.with_context(all_locations=True)
        return super(Website, self)._get_warehouse_available()
