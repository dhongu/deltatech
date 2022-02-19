# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleBillingAddresses(WebsiteSale):
    def checkout_values(self, **kw):
        values = super(WebsiteSaleBillingAddresses, self).checkout_values(**kw)
        order = request.website.sale_get_order(force_create=1)
        billings_addresses = []
        if order.partner_id != request.website.user_id.sudo().partner_id:
            Partner = order.partner_id.with_context(show_address=1).sudo()
            billings_addresses = Partner.search(
                [
                    "|",
                    ("access_for_user_id", "=", request.env.user.id),
                    ("id", "child_of", order.partner_id.commercial_partner_id.ids),
                    ("type", "in", ["invoice"]),
                    # ("id", "=", order.partner_id.commercial_partner_id.id),
                ],
                order="id desc",
            )
            if billings_addresses:
                if kw.get("partner_id") or kw.get("type") == "invoice":
                    partner_id = int(kw.get("partner_id"))
                    if partner_id in billings_addresses.mapped("id"):
                        order.partner_invoice_id = partner_id

        values["billings_addresses"] = billings_addresses
        return values

    def values_postprocess(self, order, mode, values, errors, error_msg):
        new_values, errors, error_msg = super(WebsiteSaleBillingAddresses, self).values_postprocess(
            order, mode, values, errors, error_msg
        )
        if values.get("type", False):
            new_values["type"] = values.get("type")
        if mode == ("new", "invoice"):
            new_values["parent_id"] = order.partner_id.commercial_partner_id.id

        if values.get("vat", False):
            domain = [("parent_id", "=", False), ("vat", "=", values["vat"])]
            parent = request.env["res.partner"].sudo().search(domain)
            if parent:
                new_values["parent_id"] = parent.id

        if not new_values.get("parent_id", False):
            new_values["is_company"] = values.get("is_company", False) == "on"
        new_values["access_for_user_id"] = request.env.user.id

        return new_values, errors, error_msg

    @http.route()
    def address(self, **kw):
        if kw.get("type") == "invoice" and "submitted" in kw and request.httprequest.method == "POST":
            return self.billing_address(**kw)
        return super(WebsiteSaleBillingAddresses, self).address(**kw)

    @http.route(
        ["/shop/billing_address"], type="http", methods=["GET", "POST"], auth="public", website=True, sitemap=False
    )
    def billing_address(self, **kw):
        Partner = request.env["res.partner"].with_context(show_address=1).sudo()
        order = request.website.sale_get_order()

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        mode = (False, False)
        can_edit_vat = False
        values, errors = {}, {}

        partner_id = int(kw.get("partner_id", -1))

        # IF PUBLIC ORDER
        if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
            mode = ("new", "billing")
            can_edit_vat = True
        # IF ORDER LINKED TO A PARTNER
        else:
            if partner_id > 0:
                mode = ("edit", "billing")
                if partner_id == order.partner_invoice_id.id:
                    can_edit_vat = order.partner_invoice_id.can_edit_vat()
                if mode and partner_id != -1:
                    values = Partner.browse(partner_id)

            elif partner_id == -1:
                mode = ("new", "invoice")
            else:  # no mode - refresh without post?
                return request.redirect("/shop/checkout")

        # IF POSTED
        if "submitted" in kw and request.httprequest.method == "POST":
            pre_values = self.values_preprocess(order, mode, kw)
            errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
            post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)

            if errors:
                errors["error_message"] = error_msg
                values = kw
            else:
                partner_id = self._checkout_billing_form_save(mode, post, kw)
                order.partner_invoice_id = partner_id
                # order.with_context(not_self_saleperson=True).onchange_partner_id()

                # TDE FIXME: don't ever do this
                # -> TDE: you are the guy that did what we should never do in commit e6f038a
                order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
                if not errors:
                    return request.redirect(kw.get("callback") or "/shop/checkout")

        render_values = {
            "website_sale_order": order,
            "partner_id": partner_id,
            "mode": mode,
            "checkout": values,
            "can_edit_vat": True,
            "error": errors,
            "callback": kw.get("callback"),
            "only_services": order and order.only_services,
            "type": "invoice",
            "use_same": False,
        }
        render_values.update(self._get_country_related_render_values(kw, render_values))
        return request.render("website_sale.address", render_values)

    def _checkout_billing_form_save(self, mode, checkout, all_values):
        Partner = request.env["res.partner"]
        partner_id = False
        if mode[0] == "new":
            partner_id = Partner.sudo().with_context(tracking_disable=True).create(checkout).id
        elif mode[0] == "edit":
            partner_id = int(all_values.get("partner_id", 0))
            if partner_id:
                Partner.browse(partner_id).sudo().write(checkout)
        return partner_id
