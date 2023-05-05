# ©  2015-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class Website(models.Model):
    _inherit = "website"

    def _search_get_details(self, search_type, order, options):
        result = super()._search_get_details(search_type, order, options)
        if search_type in ["vendor_product", "all"]:
            result.append(self.env["vendor.product"]._search_get_detail(self, order, options))
        return result
