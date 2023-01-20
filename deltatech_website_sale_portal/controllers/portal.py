# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, http
from odoo.http import request
from odoo.osv import expression

from odoo.addons.sale.controllers import portal


class CustomerPortal(portal.CustomerPortal):
    def _get_sale_searchbar_sortings(self):
        sortings = super(CustomerPortal, self)._get_sale_searchbar_sortings()
        sortings.update(
            {
                "name": {"label": _("Order Name"), "order": "name"},
                "client_order_ref": {"label": _("Client Reference"), "order": "client_order_ref"},
            }
        )
        return sortings

    def _prepare_quotations_domain(self, partner):
        domain = super(CustomerPortal, self)._prepare_quotations_domain(partner)
        domain = self._prepare_domain_search(domain)
        return domain

    def _prepare_orders_domain(self, partner):
        domain = super(CustomerPortal, self)._prepare_orders_domain(partner)
        domain = self._prepare_domain_search(domain)
        return domain

    def _prepare_domain_search(self, domain):
        if "search" in request.params and request.params["search"]:
            search = request.params["search"]
            if search:
                search_in = request.params.get("search_in", "all")

                if search_in == "name":
                    domain = expression.AND([domain, [("name", "ilike", search)]])
                if search_in == "client_order_ref":
                    domain = expression.AND([domain, [("client_order_ref", "ilike", search)]])
                if search_in == "all":
                    domain = expression.AND(
                        [domain, ["|", ("name", "ilike", search), ("client_order_ref", "ilike", search)]]
                    )
        return domain

    @http.route()
    def portal_my_quotes(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        result = super(CustomerPortal, self).portal_my_quotes(
            page=page, date_begin=date_begin, date_end=date_end, sortby=sortby, **kw
        )

        searchbar_inputs = {
            "client_order_ref": {"label": _("Search in Client Reference"), "input": "client_order_ref"},
            "name": {"label": _("Search in Name"), "input": "name"},
            "all": {"label": _("Search in All"), "input": "all"},
        }

        result.qcontext["searchbar_inputs"] = searchbar_inputs
        result.qcontext["search_in"] = request.params.get("search_in", "all")
        return result

    @http.route()
    def portal_my_orders(self, page=1, date_begin=None, date_end=None, sortby=None, **kw):
        result = super(CustomerPortal, self).portal_my_orders(
            page=page, date_begin=date_begin, date_end=date_end, sortby=sortby, **kw
        )

        searchbar_inputs = {
            "client_order_ref": {"label": _("Search in Client Reference"), "input": "client_order_ref"},
            "name": {"label": _("Search in Name"), "input": "name"},
            "all": {"label": _("Search in All"), "input": "all"},
        }

        result.qcontext["searchbar_inputs"] = searchbar_inputs
        result.qcontext["search_in"] = request.params.get("search_in", "all")
        return result
