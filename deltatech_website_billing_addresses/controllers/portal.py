# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from markupsafe import Markup

from odoo import _, http
from odoo.http import request
from odoo.osv import expression

from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class CustomerPortal(portal.CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super(CustomerPortal, self)._prepare_home_portal_values(counters)
        if "billing_addresses_count" in counters:
            domain = self._get_portal_billing_addresses_domain()
            values["billing_addresses_count"] = request.env["res.partner"].sudo().search_count(domain)

        if "shipping_addresses_count" in counters:
            domain = self._get_portal_shipping_addresses_domain()
            values["shipping_addresses_count"] = request.env["res.partner"].sudo().search_count(domain)
        return values

    def _get_portal_billing_addresses_domain(self):
        partner_id = request.env.user.partner_id
        domain = [("access_for_user_id", "=", request.env.user.id)]
        domain = expression.OR([domain, [("id", "child_of", partner_id.commercial_partner_id.ids)]])
        domain = expression.AND([domain, [("type", "in", ["invoice"])]])

        return domain

    def _get_portal_shipping_addresses_domain(self):
        partner_id = request.env.user.partner_id
        domain = [("access_for_user_id", "=", request.env.user.id)]
        domain = expression.OR([domain, [("id", "child_of", partner_id.commercial_partner_id.ids)]])
        domain = expression.AND([domain, [("type", "in", ["delivery"])]])
        return domain

    @http.route(
        ["/my/billing_addresses", "/my/billing_addresses/page/<int:page>"], type="http", auth="user", website=True
    )
    def portal_my_billing_addresses(
        self,
        page=1,
        date_begin=None,
        date_end=None,
        sortby=None,
        search=None,
        search_in="all",
        groupby="none",
        filterby=None,
        **kw
    ):
        values = self._prepare_portal_layout_values()

        domain = self._get_portal_billing_addresses_domain()

        ResPartner = request.env["res.partner"].sudo()

        searchbar_sortings = {
            # 'name': {'label': _('Name'), 'order': 'name'},
        }

        searchbar_filters = {
            "all": {"label": _("All"), "domain": []},
        }

        searchbar_inputs = {
            "all": {"input": "all", "label": Markup(_('Search <span class="nolabel"> (in Document)</span>'))},
        }

        searchbar_groupby = {
            "none": {"label": _("None"), "input": "none"},
        }

        pager = portal_pager(
            url="/my/billing_addresses",
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
                "filterby": filterby,
                "search_in": search_in,
                "search": search,
            },
            total=ResPartner.search_count(domain),
            page=page,
            step=self._items_per_page,
        )
        order = "name"

        billing_addresses = ResPartner.search(domain, order=order, limit=self._items_per_page, offset=pager["offset"])

        values.update(
            {
                "date": date_begin,
                "billing_addresses": billing_addresses,
                "page_name": "billing_addresses",
                "pager": pager,
                "default_url": "/my/billing_addresses",
                "searchbar_sortings": searchbar_sortings,
                "searchbar_filters": searchbar_filters,
                "searchbar_groupby": searchbar_groupby,
                "searchbar_inputs": searchbar_inputs,
                "search_in": search_in,
                "groupby": groupby,
                "sortby": sortby,
                "filterby": filterby,
            }
        )
        return request.render("deltatech_website_billing_addresses.billing_addresses_portal_my_requests", values)

    @http.route(
        ["/my/shipping_addresses", "/my/shipping_addresses/page/<int:page>"], type="http", auth="user", website=True
    )
    def portal_my_shipping_addresses(
        self,
        page=1,
        date_begin=None,
        date_end=None,
        sortby=None,
        search=None,
        search_in="all",
        groupby="none",
        filterby=None,
        **kw
    ):
        values = self._prepare_portal_layout_values()

        domain = self._get_portal_shipping_addresses_domain()

        ResPartner = request.env["res.partner"].sudo()

        searchbar_sortings = {
            # 'name': {'label': _('Name'), 'order': 'name'},
        }

        searchbar_filters = {
            "all": {"label": _("All"), "domain": []},
        }

        searchbar_inputs = {
            "all": {"input": "all", "label": Markup(_('Search <span class="nolabel"> (in Document)</span>'))},
        }

        searchbar_groupby = {
            "none": {"label": _("None"), "input": "none"},
        }

        pager = portal_pager(
            url="/my/shipping_addresses",
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
                "filterby": filterby,
                "search_in": search_in,
                "search": search,
            },
            total=ResPartner.search_count(domain),
            page=page,
            step=self._items_per_page,
        )
        order = "name"

        shipping_addresses = ResPartner.search(domain, order=order, limit=self._items_per_page, offset=pager["offset"])

        values.update(
            {
                "date": date_begin,
                "shipping_addresses": shipping_addresses,
                "page_name": "shipping_addresses",
                "pager": pager,
                "default_url": "/my/shipping_addresses",
                "searchbar_sortings": searchbar_sortings,
                "searchbar_filters": searchbar_filters,
                "searchbar_groupby": searchbar_groupby,
                "searchbar_inputs": searchbar_inputs,
                "search_in": search_in,
                "groupby": groupby,
                "sortby": sortby,
                "filterby": filterby,
            }
        )
        return request.render("deltatech_website_billing_addresses.shipping_addresses_portal_my_requests", values)
