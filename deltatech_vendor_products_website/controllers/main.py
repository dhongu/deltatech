# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import http
from odoo.http import request

from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.portal.controllers.portal import _build_url_w_params


class WebsiteVendorProduct(http.Controller):
    @http.route(
        '/vendor_product/<model("vendor.product"):vendor_product>',
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def vendor_product(self, vendor_product=None, search=None, **opt):
        if not vendor_product:
            return request.not_found()
        if not vendor_product.product_id:
            vendor_product.create_product()
        product = vendor_product.product_tmpl_id
        return request.redirect(_build_url_w_params("/shop/%s" % slug(product), request.params), code=301)
