# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.http import request

from odoo.addons.phone_validation.tools import phone_validation
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSalePhoneValidation(WebsiteSale):
    def checkout_form_validate(self, mode, all_form_values, data):

        error = dict()
        error_message = []

        if data.get("phone"):
            data["phone"] = data.get("phone").strip()

        standard_error, standard_error_message = super(WebsiteSalePhoneValidation, self).checkout_form_validate(
            mode, all_form_values, data
        )

        error.update(standard_error)
        error_message += standard_error_message

        if data.get("phone"):
            try:
                phone = data.get("phone")
                country = request.env["res.country"].sudo().browse(data.get("country_id"))
                data["phone"] = phone_validation.phone_format(
                    phone,
                    country.code if country else None,
                    country.phone_code if country else None,
                    force_format="INTERNATIONAL",
                    raise_exception=True,
                )
            except Exception as e:
                error["phone"] = "error"
                error_message.append(e.name)

        return error, error_message
