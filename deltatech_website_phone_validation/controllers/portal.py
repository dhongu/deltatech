# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.http import request

from odoo.addons.phone_validation.tools import phone_validation
from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalPhoneValidation(CustomerPortal):
    def details_form_validate(self, data):

        if data.get("phone"):
            data["phone"] = data.get("phone").strip()

        error, error_message = super(CustomerPortalPhoneValidation, self).details_form_validate(data)

        if data.get("phone"):
            try:
                phone = data.get("phone")

                country = request.env["res.country"].sudo().browse(int(data.get("country_id")))
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
