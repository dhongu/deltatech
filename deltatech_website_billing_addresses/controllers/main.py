# ©  2008-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import http
from odoo.http import request
from odoo.osv import expression

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleBillingAddresses(WebsiteSale):
    def checkout_form_validate(self, mode, all_form_values, data):
        error, error_message = super(WebsiteSaleBillingAddresses, self).checkout_form_validate(
            mode, all_form_values, data
        )
        is_company = data.get("is_company", False) == "yes"
        if is_company and not data.get("vat", False):
            error["vat"] = "missing"
        return error, error_message

    def _get_mandatory_fields_billing(self, country_id=False):
        res = super()._get_mandatory_fields_billing(country_id)
        res.remove("name")
        res.remove("email")

        return res

    @http.route()
    def checkout(self, **post):
        post.pop("express", False)
        new_context = dict(request.env.context, ignore_check_address=True)
        request.context = new_context
        return super(WebsiteSaleBillingAddresses, self).checkout(**post)

    def checkout_values(self, **kw):
        values = super(WebsiteSaleBillingAddresses, self).checkout_values(**kw)
        order = request.website.sale_get_order(force_create=1)
        billings_addresses = []
        if order.partner_id != request.website.user_id.sudo().partner_id:
            Partner = order.partner_id.with_context(show_address=1).sudo()

            domain = [("access_for_user_id", "=", request.env.user.id)]
            domain = expression.OR([domain, [("user_id", "=", request.env.user.id)]])
            domain = expression.OR([domain, [("id", "child_of", order.partner_id.commercial_partner_id.ids)]])
            domain = expression.AND([domain, [("type", "in", ["invoice"])]])
            domain = expression.OR([domain, [("id", "in", [order.partner_invoice_id.id, order.partner_id.id])]])

            billings_addresses = Partner.search(domain, order="id desc")
            if billings_addresses:
                if kw.get("partner_id") or kw.get("type") == "invoice":
                    partner_id = int(kw.get("partner_id"))
                    if partner_id in billings_addresses.mapped("id"):
                        order.partner_invoice_id = partner_id

        values["billings_addresses"] = billings_addresses
        shippings = values.get("shippings", [])
        if shippings and len(shippings) > 1:
            values["shippings"] = shippings.filtered(lambda p: p.type == "delivery")
        return values

    def values_postprocess(self, order, mode, values, errors, error_msg):
        new_values, errors, error_msg = super(WebsiteSaleBillingAddresses, self).values_postprocess(
            order, mode, values, errors, error_msg
        )
        errors.pop("vat", "")  # sa scrie fiecare ce vrea
        is_company = values.get("is_company", False) == "yes"

        if values.get("type", False):
            new_values["type"] = values.get("type")
        if mode[0] == "new":
            new_values["parent_id"] = order.partner_id.commercial_partner_id.id

        if values.get("vat", False) and is_company:
            domain = [("parent_id", "=", False), ("vat", "=", values["vat"])]
            parent = request.env["res.partner"].sudo().search(domain, limit=1)
            if not parent:
                parent = (
                    request.env["res.partner"]
                    .sudo()
                    .with_context(tracking_disable=True, no_vat_validation=True)
                    .create(
                        {
                            "name": values["company_name"] or values["name"],
                            "vat": values["vat"],
                            "is_company": True,
                            "street": values.get("street", False),
                            "street2": values.get("street2", False),
                            "city": values.get("city", False),
                            "state_id": values.get("state_id", False),
                            "country_id": values.get("country_id", False),
                            "phone": values.get("phone", False),
                            "email": values.get("email", False),
                        }
                    )
                )
            new_values["name"] = request.env.user.name
            new_values["parent_id"] = parent.id

        if not new_values.get("parent_id", False):
            new_values["is_company"] = is_company
        new_values["access_for_user_id"] = request.env.user.id

        return new_values, errors, error_msg

    @http.route()
    def address(self, **kw):
        request.website.sale_get_order(force_create=True)
        if kw.get("type") == "invoice" and "submitted" in kw and request.httprequest.method == "POST":
            return self.billing_address(**kw)
        return super(WebsiteSaleBillingAddresses, self).address(**kw)

    @http.route(
        ["/shop/billing_address"], type="http", methods=["GET", "POST"], auth="public", website=True, sitemap=False
    )
    def billing_address(self, **kw):
        Partner = request.env["res.partner"].with_context(show_address=1).sudo()
        order = request.website.sale_get_order(force_create=True)

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        # mode = (False, False)
        can_edit_vat = False
        values, errors = {}, {}

        partner_id = int(kw.get("partner_id", -1))
        is_company = request.httprequest.args.get("is_company", "no")

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
                    if values.commercial_partner_id.is_company:
                        is_company = "yes"

            elif partner_id == -1:
                mode = ("new", "billing")
                # is_company = 'yes'
                # values = {"is_company": True}
                can_edit_vat = True
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

        if is_company == "no":
            can_edit_vat = False
        else:
            values["is_company"] = True

        render_values = {
            "website_sale_order": order,
            "partner_id": partner_id,
            "mode": mode,
            "checkout": values,
            "can_edit_vat": can_edit_vat,
            "error": errors,
            "callback": kw.get("callback"),
            "type": "invoice",
            "use_same": False,
            "only_services": True,
            "is_company": is_company,
        }
        render_values.update(self._get_country_related_render_values(kw, render_values))
        return request.render("website_sale.address", render_values)

    def _checkout_billing_form_save(self, mode, checkout, all_values):
        Partner = request.env["res.partner"]
        partner_id = False
        if mode[0] == "new":
            partner_id = Partner.sudo().with_context(tracking_disable=True, no_vat_validation=True).create(checkout).id
        elif mode[0] == "edit":
            partner_id = int(all_values.get("partner_id", 0))
            if partner_id:
                Partner.browse(partner_id).sudo().write(checkout)
        return partner_id

    def checkout_check_address(self, order):
        if request.env.context.get("ignore_check_address", False):
            return
        billing_fields_required = self._get_mandatory_fields_billing(order.partner_invoice_id.country_id.id)
        if not all(order.partner_invoice_id.read(billing_fields_required)[0].values()):
            return request.redirect("/shop/address?partner_id=%d" % order.partner_invoice_id.id)

        shipping_fields_required = self._get_mandatory_fields_shipping(order.partner_shipping_id.country_id.id)
        if not all(order.partner_shipping_id.read(shipping_fields_required)[0].values()):
            return request.redirect("/shop/address?partner_id=%d" % order.partner_shipping_id.id)
