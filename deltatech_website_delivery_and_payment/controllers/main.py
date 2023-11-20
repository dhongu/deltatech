# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale as Base


class WebsiteSale(Base):
    @route("/shop/carrier_acquirer_check", type="json", auth="public", website=True, sitemap=False)
    def carrier_acquirer_check(self, carrier_id, provider_id=None, **kw):
        result = {"status": False, "all_acquirer": True}
        carrier = request.env["delivery.carrier"].sudo().browse(int(carrier_id))
        if provider_id is None:
            provider_id = 0
        if carrier:
            if carrier.acquirer_allowed_ids:
                result = {
                    "status": False,
                    "acquirer_allowed_ids": carrier.acquirer_allowed_ids.ids,
                    "all_acquirer": False,
                }
                if int(provider_id) in carrier.acquirer_allowed_ids.ids:
                    result["status"] = True
            else:
                result = {"status": True, "all_acquirer": True}

        if provider_id:
            # context = dict(request.context)
            # context.setdefault("provider_id", provider_id)
            # request.context = context
            request.update_context(provider_id=provider_id)
            order = request.website.sale_get_order()

            acquirer = request.env["payment.provider"].sudo().browse(int(provider_id))
            # if acquirer and order.provider_id != acquirer:
            #     order.write({"provider_id": acquirer.id})

            if acquirer.value_limit and order.amount_total > acquirer.value_limit:
                result["status"] = False
            label_ids = list(set(order.partner_id.category_id.ids) & set(acquirer.restrict_label_ids.ids))
            if label_ids:
                result["status"] = False

        return result

    @route()
    def cart_carrier_rate_shipment(self, carrier_id, **kw):
        # order = request.website.sale_get_order()
        provider_id = int(kw.get("provider_id", 0))
        if provider_id:
            # context = dict(request.context)
            # context.setdefault("provider_id", provider_id)
            # request.context = context
            request.update_context(provider_id=provider_id)
        # if provider_id:
        #     acquirer = request.env["payment.provider"].sudo().browse(int(provider_id))
        #     if acquirer and order.provider_id != acquirer:
        #         order.write({"provider_id": acquirer.provider_id})

        return super().cart_carrier_rate_shipment(carrier_id, **kw)

    def _get_shop_payment_values(self, order, **kwargs):
        values = super()._get_shop_payment_values(order, **kwargs)
        # if order.carrier_id and order.carrier_id.acquirer_allowed_ids:
        #     values["acquirer_allowed_ids"] = order.carrier_id.acquirer_allowed_ids.ids
        values["provider_id"] = order.partner_id.provider_id.id
        return values
