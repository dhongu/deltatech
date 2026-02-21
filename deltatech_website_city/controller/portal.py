# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging

from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal

_logger = logging.getLogger(__name__)


class CustomerPortalCity(CustomerPortal):
    def on_account_update(self, values, partner):
        # The base account() method only converts state_id and country_id to int.
        # We need to convert city_id as well.
        if "city_id" in values:
            try:
                values["city_id"] = int(values["city_id"])
            except (ValueError, TypeError):
                values["city_id"] = False
        return super().on_account_update(values, partner)

    def details_form_validate(self, data, **kwargs):
        if "country_id" in data:
            request.update_context(portal_form_country_id=data["country_id"])
        if "city_id" in data:
            try:
                city_id = int(data["city_id"])
                city = request.env["res.city"].sudo().browse(city_id)
                if city.exists():
                    data["city"] = city.name
                    # Also set zipcode if available in city and empty in data
                    if city.zipcode and not data.get("zipcode"):
                        data["zipcode"] = city.zipcode
            except (ValueError, TypeError):
                # We can safely ignore these errors as they correspond to invalid city IDs
                # which shouldn't be processed further.
                _logger.debug("Invalid city ID provided in form data: %s", data.get("city_id"))

        return super().details_form_validate(data, **kwargs)

    def _get_mandatory_fields(self):
        # EXTENDS 'portal'
        try:
            country_id = int(request.env.context.get("portal_form_country_id", ""))
        except ValueError:
            country_id = None

        mandatory_fields = super()._get_mandatory_fields()
        if country_id:
            country_sudo = request.env["res.country"].sudo().browse(country_id)
            if country_sudo.enforce_cities:
                if "city_id" not in mandatory_fields:
                    mandatory_fields += ["city_id"]
                if "state_id" not in mandatory_fields:
                    mandatory_fields += ["state_id"]
        return mandatory_fields

    def _get_optional_fields(self):
        # EXTENDS 'portal'
        try:
            country_id = int(request.env.context.get("portal_form_country_id", ""))
        except ValueError:
            country_id = None

        optional_fields = super()._get_optional_fields()
        if country_id:
            country_sudo = request.env["res.country"].sudo().browse(country_id)
            if country_sudo.enforce_cities:
                optional_fields = [field for field in optional_fields if field not in ["city_id", "state_id"]]
        if "city_id" not in optional_fields and "city_id" not in self._get_mandatory_fields():
            optional_fields.append("city_id")

        # Odoo portal account uses 'zipcode' in the form but saves to 'zip' on the partner.
        # But for 'city_id', it's normally not in the base portal fields.
        return optional_fields
