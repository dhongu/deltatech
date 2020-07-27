from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import fields, http, tools, _


class WebsiteSaleCity(WebsiteSale):

    # pentru tarile in care nu avam nomencator de localitati nu se poate face acest camp obligatori
    # def _get_mandatory_billing_fields(self):
    #     res = super(WebsiteSaleCity, self)._get_mandatory_billing_fields()
    #     res += ['city_id']
    #     res.remove('city')
    #     return res
    #
    # def _get_mandatory_shipping_fields(self):
    #     res = super(WebsiteSaleCity, self)._get_mandatory_shipping_fields()
    #     res += ['city_id']
    #     res.remove('city')
    #     return res

    def values_postprocess(self, order, mode, values, errors, error_msg):
        new_values, errors, error_msg = super(WebsiteSaleCity, self).values_postprocess(order, mode, values, errors, error_msg)
        new_values['city_id'] = values.get('city_id')
        return new_values, errors, error_msg