# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from collections import OrderedDict

from odoo import _, http
from odoo.http import request

from odoo.addons.account.controllers.portal import PortalAccount
from odoo.addons.portal.controllers.portal import pager as portal_pager


class PortalAccountInherit(PortalAccount):
    @http.route(["/my/invoices_in", "/my/invoices_in/page/<int:page>"], type="http", auth="user", website=True)
    def portal_my_invoices_in(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        return self.portal_my_invoices(page, date_begin, date_end, sortby, filterby="bills", **kw)

    @http.route(["/my/invoices_out", "/my/invoices_out/page/<int:page>"], type="http", auth="user", website=True)
    def portal_my_invoices_out(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        return self.portal_my_invoices(page, date_begin, date_end, sortby, filterby="invoices", **kw)

    @http.route(["/my/invoices", "/my/invoices/page/<int:page>"], type="http", auth="user", website=True)
    def portal_my_invoices(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        AccountInvoice = request.env["account.invoice"]

        domain = []

        searchbar_sortings = {
            "date": {"label": _("Invoice Date"), "order": "date_invoice desc"},
            "duedate": {"label": _("Due Date"), "order": "date_due desc"},
            "name": {"label": _("Reference"), "order": "name desc"},
            "state": {"label": _("Status"), "order": "state"},
        }
        # default sort by order
        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]

        archive_groups = self._get_archive_groups("account.invoice", domain)
        if date_begin and date_end:
            domain += [("create_date", ">", date_begin), ("create_date", "<=", date_end)]

        #  adaugare filtrare
        searchbar_filters = {
            "all": {"label": _("All"), "domain": []},
            "invoices": {"label": _("Invoices"), "domain": [("type", "=", ("out_invoice", "out_refund"))]},
            "bills": {"label": _("Bills"), "domain": [("type", "=", ("in_invoice", "in_refund"))]},
        }
        # default filter by value
        if not filterby:
            filterby = "all"
        domain += searchbar_filters[filterby]["domain"]
        # adaugare filtrare

        # count for pager
        invoice_count = AccountInvoice.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/invoices",
            url_args={"date_begin": date_begin, "date_end": date_end, "sortby": sortby},
            total=invoice_count,
            page=page,
            step=self._items_per_page,
        )
        # content according to pager and archive selected
        invoices = AccountInvoice.search(domain, order=order, limit=self._items_per_page, offset=pager["offset"])
        request.session["my_invoices_history"] = invoices.ids[:100]

        values.update(
            {
                "date": date_begin,
                "invoices": invoices,
                "page_name": "invoice",
                "pager": pager,
                "archive_groups": archive_groups,
                "default_url": "/my/invoices",
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
                #   adaugare filtrare
                "searchbar_filters": OrderedDict(sorted(searchbar_filters.items())),
                "filterby": filterby,
                #  adaugare filtrare
            }
        )
        return request.render("account.portal_my_invoices", values)
