# Copyright 2015, 2017 Jairo Llopis <jairo.llopis@tecnativa.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.http import request, route
from odoo.addons.website_sale.controllers.main import WebsiteSale as Base
from odoo.http import request


class WebsiteSale(Base):

    @route('/shop/carrier_acquirer_check', type='json')
    def carrier_acquirer_check(self, carrier_id, acquirer_id, **kw):
        result = {'status': False}
        carrier = request.env['delivery.carrier'].browse(int(carrier_id))
        if carrier:
            if carrier.acquirer_allowed_ids:
                if int(acquirer_id) in carrier.acquirer_allowed_ids.ids:
                    result = {'status': True}
            else:
                result = {'status': True}
        return result
