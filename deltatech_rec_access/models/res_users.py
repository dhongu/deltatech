# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class Users(models.Model):
    _inherit = "res.users"

    def revoke_rights(self):
        self.write({"groups_id": [(5, False, False)]})
