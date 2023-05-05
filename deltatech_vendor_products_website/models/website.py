# ©  2015-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, models

from odoo.addons.http_routing.models.ir_http import url_for


class Website(models.Model):
    _inherit = "website"

    def get_suggested_controllers(self):
        suggested_controllers = super(Website, self).get_suggested_controllers()
        suggested_controllers.append(
            (_("Vendor Products"), url_for("/vendor_product"), "deltatech_vendor_products_website")
        )
        return suggested_controllers

    def _search_get_details(self, search_type, order, options):
        result = super()._search_get_details(search_type, order, options)
        if search_type in ["vendor_product", "all"]:
            result.append(self.env["vendor.product"]._search_get_detail(self, order, options))
        return result
