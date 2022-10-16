# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import http

from odoo.addons.account.controllers.portal import PortalAccount


class PortalAccountInherit(PortalAccount):
    @http.route(["/my/invoices_in", "/my/invoices_in/page/<int:page>"], type="http", auth="user", website=True)
    def portal_my_invoices_in(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        return self.portal_my_invoices(page, date_begin, date_end, sortby, filterby="bills", **kw)

    @http.route(["/my/invoices_out", "/my/invoices_out/page/<int:page>"], type="http", auth="user", website=True)
    def portal_my_invoices_out(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        return self.portal_my_invoices(page, date_begin, date_end, sortby, filterby="invoices", **kw)
