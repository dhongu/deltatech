# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

import requests

from odoo import fields
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale

_logger = logging.getLogger(__name__)

ANAF_URL = "https://webservicesp.anaf.ro/api/PlatitorTvaRest/v9/tva"
# the customer waits at the checkout: better accept the number than keep them 30 s
ANAF_TIMEOUT = 5
# check digit weights of the Romanian personal numeric code (CNP)
CNP_WEIGHTS = (2, 7, 9, 1, 4, 6, 3, 5, 8, 2, 7, 9)


def normalize_vat(vat):
    """``RO 12 34 567``, ``ro1234567`` and ``1234567`` are the same tax code: letters and digits
    only, upper case, without a two-letter country prefix."""
    vat = "".join(ch for ch in (vat or "") if ch.isalnum()).upper()
    if len(vat) > 2 and vat[:2].isalpha():
        vat = vat[2:]
    return vat


def is_cnp(number):
    """Whether ``number`` is a valid Romanian personal numeric code (13 digits, check digit)."""
    if len(number) != 13 or not number.isdigit() or number[0] not in "12345678":
        return False
    rest = sum(int(number[i]) * CNP_WEIGHTS[i] for i in range(12)) % 11
    return int(number[12]) == (1 if rest == 10 else rest)


class WebsiteSaleVATValidation(WebsiteSale):
    def _validate_address_values(
        self,
        address_values,
        partner_sudo,
        address_type,
        use_delivery_as_billing,
        required_fields,
        **_kwargs,
    ):
        for field in ["vat", "email", "phone"]:
            if address_values.get(field):
                address_values[field] = address_values.get(field).strip()

        invalid_fields, missing_fields, error_messages = super()._validate_address_values(
            address_values=address_values,
            partner_sudo=partner_sudo,
            address_type=address_type,
            use_delivery_as_billing=use_delivery_as_billing,
            required_fields=required_fields,
            **_kwargs,
        )
        partner = partner_sudo or request.env.user.partner_id

        # Integrare ANAF
        if address_values.get("vat") and "vat" not in invalid_fields:
            if address_type == "billing" or use_delivery_as_billing:
                country = request.env["res.country"].sudo().browse(address_values.get("country_id"))
                if country and country.code == "RO":
                    vat = address_values["vat"].strip().upper()
                    if vat.startswith("RO"):
                        vat = vat[2:]
                    if is_cnp(vat):
                        # a person who buys for themselves types their CNP here: ANAF would not
                        # find it as a company, and the message would send them looking for an error
                        invalid_fields.add("vat")
                        error_messages.append(
                            request.env._(
                                "This looks like a personal numeric code (CNP). This field is for the "
                                "tax code (CUI) of a company; if you buy as an individual, leave it empty."
                            )
                        )
                    elif vat.isdigit():
                        res_partner_sudo = request.env["res.partner"].sudo()
                        if hasattr(res_partner_sudo, "_Anaf_to_Odoo"):
                            state, anaf_data = self._anaf_lookup(vat)
                            if state == "found":
                                # Actualizăm valorile adresei cu datele de la ANAF
                                for field in ["name", "street", "city", "zip"]:
                                    if anaf_data.get(field):
                                        address_values[field] = anaf_data[field]
                                if anaf_data.get("state_id") and not address_values.get("state_id"):
                                    address_values["state_id"] = anaf_data["state_id"].id

                                if anaf_data.get("company_type") == "company":
                                    address_values["is_company"] = True
                            elif state == "not_found":
                                invalid_fields.add("vat")
                                error_messages.append(request.env._("The VAT number is not valid according to ANAF"))
                            else:
                                # ANAF does not answer: the sale goes on with the number as typed
                                # (its format is checked above) and the salesperson is told
                                self._anaf_unavailable_note(address_values["vat"])
                    else:
                        invalid_fields.add("vat")
                        error_messages.append(
                            request.env._("The VAT number must contain only digits (after the country code)")
                        )

        # Verificarea de duplicat nu se face pentru vizitatorul anonim: mesajul ar
        # confirma oricui că un email/telefon/CUI aparține unui client existent
        # (oracol de enumerare). Fluxul standard de guest checkout rămâne neatins.
        if request.env.user._is_public():
            return invalid_fields, missing_fields, error_messages

        # The company of the customer and its contacts are not duplicates. The phone is not
        # checked: colleagues share the company phone, relatives share a home phone. The
        # messages do not name the account found.
        own_company = partner.commercial_partner_id
        vat = address_values.get("vat")
        if vat and "vat" not in invalid_fields and self._vat_duplicate(vat, own_company):
            invalid_fields.add("vat")
            error_messages.append(self._vat_duplicate_message())
        email = address_values.get("email")
        if email and "email" not in invalid_fields:
            domain = [
                ("email", "=", email),
                ("parent_id", "=", False),
                ("commercial_partner_id", "!=", own_company.id),
            ]
            if request.env["res.partner"].sudo().search_count(domain, limit=1):
                invalid_fields.add("email")
                error_messages.append(
                    request.env._(
                        "This e-mail address belongs to another account. "
                        "Log in with that account or use another address."
                    )
                )

        return invalid_fields, missing_fields, error_messages

    def _vat_duplicate(self, vat, own_company):
        """Whether another customer has this tax code, written with or without its country prefix."""
        key = normalize_vat(vat)
        if not key:
            return False
        # the stored code may carry a prefix or spaces: search on its last digits, which any
        # spelling keeps together, then compare the normalised forms
        candidates = (
            request.env["res.partner"]
            .sudo()
            .search(
                [
                    ("vat", "ilike", key[-3:]),
                    ("parent_id", "=", False),
                    ("commercial_partner_id", "!=", own_company.id),
                ]
            )
        )
        return any(normalize_vat(candidate.vat) == key for candidate in candidates)

    def _vat_duplicate_message(self):
        """What a customer can do when their company already has an account."""
        if "b2b_state" in request.env["res.partner"]._fields:
            # deltatech_b2b_portal: its form recognises the company by its tax code, adds only the
            # contact and gives the salesperson an activity: an access request
            return request.env._(
                "A company with this tax code already has an account with us. To order on its "
                "behalf, ask a colleague who has access to add you, or send an access request "
                "from %(url)s.",
                url=f"{request.httprequest.host_url.rstrip('/')}/b2b",
            )
        return request.env._(
            "A company with this tax code already has an account with us. To order on its "
            "behalf, ask a colleague who has access to add you, or contact us."
        )

    def _anaf_lookup(self, vat):
        """Look ``vat`` up at ANAF.

        Its own request rather than ``_get_Anaf`` of ``l10n_ro_partner_create_by_vat``: that one
        waits up to 30 s and answers the same text for a company not found and for a service
        down, while the checkout must tell them apart. The settings are the same.

        :return: ``(state, values)``: ``found`` with the partner values, ``not_found`` or
            ``unavailable``
        """
        partner_sudo = request.env["res.partner"].sudo()
        test_data = request.env.context.get("anaf_data")
        if test_data is not None:
            result = test_data.get(vat)
            if not result:
                return "not_found", {}
            if result.get("unavailable"):
                return "unavailable", {}
            return "found", partner_sudo._Anaf_to_Odoo(result)
        get_param = request.env["ir.config_parameter"].sudo().get_param
        headers = {"Content-Type": "application/json"}
        api_key = get_param("l10n_ro_partner_create_by_vat.anaf_api_key", "")
        if api_key:
            headers[get_param("l10n_ro_partner_create_by_vat.anaf_api_key_header_tag", "x-api-key")] = api_key
        try:
            response = requests.post(
                get_param("l10n_ro_partner_create_by_vat.anaf_url", ANAF_URL),
                json=[{"cui": vat, "data": fields.Date.to_string(fields.Date.today())}],
                headers=headers,
                timeout=ANAF_TIMEOUT,
            )
            response.raise_for_status()
            found = response.json().get("found") or []
        except (requests.RequestException, ValueError) as error:
            _logger.warning("ANAF did not answer for the VAT number %s: %s", vat, error)
            return "unavailable", {}
        result = found[0] if found else {}
        if not result.get("date_generale"):
            return "not_found", {}
        return "found", partner_sudo._Anaf_to_Odoo(result)

    def _anaf_unavailable_note(self, vat):
        """An internal note on the cart: its VAT number was not checked at ANAF."""
        try:
            order_sudo = request.cart
        except AttributeError:
            # no eCommerce cart on this request (portal address form)
            order_sudo = None
        if order_sudo:
            order_sudo.message_post(
                body=request.env._(
                    "The VAT number %(vat)s could not be checked at ANAF (service unavailable). "
                    "Please check the customer details.",
                    vat=vat,
                ),
                subtype_xmlid="mail.mt_note",
            )
