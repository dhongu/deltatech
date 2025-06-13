# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import http

from odoo.addons.account.controllers.portal import PortalAccount


class PortalAccountInherit(PortalAccount):
    # def _get_invoices_domain(self):
    #     return [
    #         ("state", "not in", ("cancel", "draft")),
    #         ("move_type", "in", ("out_invoice", "out_refund", "in_invoice", "in_refund", "out_receipt", "in_receipt")),
    #     ]

    @http.route(["/my/invoices_in", "/my/invoices_in/page/<int:page>"], type="http", auth="user", website=True)
    def portal_my_invoices_in(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        return self.portal_my_invoices(page, date_begin, date_end, sortby, filterby="bills", **kw)

    @http.route(["/my/invoices_out", "/my/invoices_out/page/<int:page>"], type="http", auth="user", website=True)
    def portal_my_invoices_out(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        return self.portal_my_invoices(page, date_begin, date_end, sortby, filterby="invoices", **kw)
