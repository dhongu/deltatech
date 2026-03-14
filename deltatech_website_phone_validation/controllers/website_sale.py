# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.http import request

from odoo.addons.phone_validation.tools import phone_validation
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSalePhoneValidation(WebsiteSale):
    def _validate_address_values(
        self,
        address_values,
        partner_sudo,
        address_type,
        use_delivery_as_billing,
        required_fields,
        is_main_address,
        **_kwargs,
    ):
        if address_values.get("phone"):
            address_values["phone"] = address_values.get("phone").strip()

        invalid_fields, missing_fields, error_messages = super()._validate_address_values(
            address_values,
            partner_sudo,
            address_type,
            use_delivery_as_billing,
            required_fields,
            is_main_address,
            **_kwargs,
        )

        if address_values.get("phone") and "phone" not in invalid_fields:
            try:
                phone = address_values.get("phone")
                country = request.env["res.country"].sudo().browse(address_values.get("country_id"))
                address_values["phone"] = phone_validation.phone_format(
                    phone,
                    country.code if country else None,
                    country.phone_code if country else None,
                    force_format="INTERNATIONAL",
                    raise_exception=True,
                )
            except Exception as e:
                invalid_fields.add("phone")
                error_messages.append(getattr(e, "name", str(e)))

        return invalid_fields, missing_fields, error_messages
