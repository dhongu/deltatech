# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, http
from odoo.http import request

from odoo.addons.sale.controllers import portal


class CustomerPortal(portal.CustomerPortal):
    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        if "show_order_fiter" in request.env.context:
            searchbar_filters = {
                "all": {"label": _("All"), "domain": []},
                "open_order": {"label": _("Open Orders"), "domain": [("stage", "not in", ["delivered", "cancel"])]},
                "closed_order": {"label": _("Closed Orders"), "domain": [("stage", "in", ["delivered", "cancel"])]},
                "placed": {"label": _("Placed"), "domain": [("stage", "=", "placed")]},
                "in_process": {"label": _("In Process"), "domain": [("stage", "=", "in_process")]},
                "waiting": {"label": _("Waiting availability"), "domain": [("stage", "=", "waiting")]},
                "postponed": {"label": _("Postponed"), "domain": [("stage", "=", "postponed")]},
                "to_be_delivery": {"label": _("To Be Delivery"), "domain": [("stage", "=", "to_be_delivery")]},
                "in_delivery": {"label": _("In Delivery"), "domain": [("stage", "=", "in_delivery")]},
                "delivered": {"label": _("Delivered"), "domain": [("stage", "=", "delivered")]},
                "cancel": {"label": _("Canceled"), "domain": [("stage", "=", "cancel")]},
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

        filterby = request.params.get("filterby", "")
        match filterby:
            case "open_order":
                domain += [("stage", "not in", ["delivered", "cancel"])]
            case "closed_order":
                domain += [("stage", "in", ["delivered", "cancel"])]
            case "placed":
                domain += [("stage", "=", "placed")]
            case "in_process":
                domain += [("stage", "=", "in_process")]
            case "waiting":
                domain += [("stage", "=", "waiting")]
            case "postponed":
                domain += [("stage", "=", "postponed")]
            case "to_be_delivery":
                domain += [("stage", "=", "to_be_delivery")]
            case "in_delivery":
                domain += [("stage", "=", "in_delivery")]
            case "delivered":
                domain += [("stage", "=", "delivered")]
            case "cancel":
                domain += [("stage", "=", "cancel")]
            case _:
                # Default case, no additional filter
                pass

        return domain

    @http.route()
    def portal_my_orders(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        request.update_context(show_order_fiter=True)
        if not filterby:
            filterby = "all"
        result = super().portal_my_orders(
            page=page, date_begin=date_begin, date_end=date_end, sortby=sortby, filterby=filterby, **kw
        )

        result.qcontext["filterby"] = request.params.get("filterby", "all")
        return result

    def _prepare_sale_portal_rendering_values(
        self, page=1, date_begin=None, date_end=None, sortby=None, quotation_page=False, **kwargs
    ):
        filterby = kwargs.get("filterby", "all")
        if not filterby:
            filterby = "all"
            kwargs["filterby"] = filterby

        values = super()._prepare_sale_portal_rendering_values(
            page=page, date_begin=date_begin, date_end=date_end, sortby=sortby, quotation_page=quotation_page, **kwargs
        )

        values["filterby"] = filterby
        values["pager"] = self.fix_pager_filer(values["pager"], filterby)

        return values

    def fix_pager_filer(self, pager, filterby):
        pager["page"]["url"] = pager["page"]["url"] + "&filterby=" + filterby
        pager["page_first"]["url"] = pager["page_first"]["url"] + "&filterby=" + filterby
        pager["page_start"]["url"] = pager["page_start"]["url"] + "&filterby=" + filterby
        pager["page_previous"]["url"] = pager["page_previous"]["url"] + "&filterby=" + filterby
        pager["page_next"]["url"] = pager["page_next"]["url"] + "&filterby=" + filterby
        pager["page_end"]["url"] = pager["page_end"]["url"] + "&filterby=" + filterby
        pager["page_last"]["url"] = pager["page_last"]["url"] + "&filterby=" + filterby
        for page in pager["pages"]:
            page["url"] = page["url"] + "&filterby=" + filterby
        return pager
