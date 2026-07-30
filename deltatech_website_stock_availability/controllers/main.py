from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers import main


class WebsiteSale(main.WebsiteSale):
    @http.route()
    def shop(self, **kwargs):
        # No parameter is restated here on purpose. The previous signature was
        # ``(page, category, search, ppg)`` and forwarded those positionally,
        # but core grew ``min_price``/``max_price`` in fourth and fifth place,
        # so ``ppg`` landed in ``min_price``: a visitor passing ``?ppg=40`` got
        # the catalogue silently filtered to products over 40 while the page
        # size stayed at its default. Odoo always invokes endpoints as
        # ``endpoint(**request.params)`` (``odoo/http.py``), so accepting
        # ``**kwargs`` and forwarding it is both correct and immune to any
        # further signature change — including 19.0, where ``ppg`` became
        # ``tags``.
        response = super().shop(**kwargs)
        availability_all = request.httprequest.args.get("availability_all", True)
        availability_in_stock = request.httprequest.args.get("availability_in_stock", False)
        availability_vendor = request.httprequest.args.get("availability_vendor", False)
        response.qcontext.update(
            availability_all=availability_all,
            availability_in_stock=availability_in_stock,
            availability_vendor=availability_vendor,
        )

        return response
