from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers import main


class WebsiteSale(main.WebsiteSale):
    @http.route()
    def shop(self, **kwargs):
        # No parameter is restated here on purpose. The previous signature was
        # ``(page, category, search, ppg)`` and forwarded those positionally,
        # but core's fourth slot is ``min_price``, so ``ppg`` landed there: a
        # visitor passing ``?ppg=40`` got the catalogue silently filtered to
        # products over 40 while the page size stayed at its default. On 19.0
        # ``ppg`` is not even a core parameter any more, yet declaring it here
        # still captured it and pushed it into ``min_price``.
        #
        # Odoo always invokes endpoints as ``endpoint(**request.params)``
        # (``odoo/http.py``), so accepting ``**kwargs`` and forwarding it is
        # both correct and immune to any further signature change.
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
