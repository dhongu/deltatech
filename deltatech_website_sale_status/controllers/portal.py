# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, http
from odoo.http import request

from odoo.addons.sale.controllers import portal


class CustomerPortal(portal.CustomerPortal):
    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        if "show_order_fiter" in request.context:
            searchbar_filters = {
                "open_order": {"label": _("Open Orders"), "domain": [("stage", "not in", ["delivered", "cancel"])]},
                "all": {"label": _("All"), "domain": []},
            }
            values.update(
                {
                    "searchbar_filters": searchbar_filters,
                }
            )
        return values

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

    def _prepare_orders_domain(self, partner):
        domain = super()._prepare_orders_domain(partner)
        if request.params.get("filterby", "") == "open_order":
            domain += [("stage", "not in", ["delivered", "cancel"])]
        return domain

    @http.route()
    def portal_my_orders(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        ctx = request.context.copy()
        ctx.update(show_order_fiter=True)
        request.context = ctx
        result = super().portal_my_orders(
            page=page, date_begin=date_begin, date_end=date_end, sortby=sortby, filterby=filterby, **kw
        )

        result.qcontext["filterby"] = request.params.get("filterby", "all")
        return result
