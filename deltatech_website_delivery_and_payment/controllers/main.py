# Copyright 2015, 2017 Jairo Llopis <jairo.llopis@tecnativa.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale as Base


class WebsiteSale(Base):
    @route("/shop/carrier_acquirer_check", type="json", auth="public", website=True, sitemap=False)
    def carrier_acquirer_check(self, carrier_id, acquirer_id, **kw):
        result = {"status": False}
        carrier = request.env["delivery.carrier"].sudo().browse(int(carrier_id))
        if carrier:
            if carrier.acquirer_allowed_ids:
                if int(acquirer_id) in carrier.acquirer_allowed_ids.ids:
                    result = {"status": True}
            else:
                result = {"status": True}
        if result["status"]:
            order = request.website.sale_get_order()
            acquirer = request.env["payment.acquirer"].sudo().browse(int(acquirer_id))
            if acquirer.value_limit and order.amount_total > acquirer.value_limit:
                result = {"status": False}
            label_ids = list(set(order.partner_id.category_id.ids) & set(acquirer.restrict_label_ids.ids))
            if label_ids:
                result = {"status": False}
        return result
