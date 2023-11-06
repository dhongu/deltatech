# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _

from odoo.addons.sale.controllers import portal


class CustomerPortal(portal.CustomerPortal):
    def _get_sale_searchbar_sortings(self):
        sortings = super()._get_sale_searchbar_sortings()
        if "stage" in sortings:
            sortings["stage"]["label"] = _("Order Status")
        sortings.update(
            {
                "order_stage": {"label": _("Order Stage"), "order": "stage"},
            }
        )
        return sortings
