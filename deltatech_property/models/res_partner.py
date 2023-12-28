# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    type = fields.Selection(selection_add=[("land", "Land"), ("building", "Building")])

    def _avatar_get_placeholder_path(self):
        if self.type == "land":
            return "deltatech_property/static/img/land.png"
        if self.type == "building":
            return "deltatech_property/static/img/building.png"
        return super()._avatar_get_placeholder_path()
