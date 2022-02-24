# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models

class View(models.Model):
    _inherit = "ir.ui.view"

    def unlink(self):
        for view in self:
            if view.exists().website_id:
                view.inherit_children_ids.unlink()

        super(View, self.exists()).unlink()
