# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalCity(CustomerPortal):
    def _get_mandatory_fields(self):
        # EXTENDS 'portal'
        try:
            country_id = int(request.env.context.get("portal_form_country_id", ""))
        except (ValueError, TypeError):
            country_id = None

        mandatory_fields = super()._get_mandatory_fields()
        if country_id:
            country_sudo = request.env["res.country"].sudo().browse(country_id)
            if country_sudo.enforce_cities:
                mandatory_fields += ["city_id", "state_id"]
                if "city" in mandatory_fields:
                    mandatory_fields.remove("city")
        return mandatory_fields

    def _get_optional_fields(self):
        # EXTENDS 'portal'
        try:
            country_id = int(request.env.context.get("portal_form_country_id", ""))
        except (ValueError, TypeError):
            country_id = None

        optional_fields = super()._get_optional_fields()
        if country_id:
            country_sudo = request.env["res.country"].sudo().browse(country_id)
            if country_sudo.enforce_cities:
                optional_fields = [field for field in optional_fields if field not in ["city_id", "state_id"]]
                if "city" not in optional_fields:
                    optional_fields.append("city")
        return optional_fields
