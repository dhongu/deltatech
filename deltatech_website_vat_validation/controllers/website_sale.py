# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale

# The Romanian checks of the tax code (ANAF, CNP, struck-off company) are in l10n_ro_website_anaf
# (l10n-romania): this module stays country-neutral.


def normalize_vat(vat):
    """``RO 12 34 567``, ``ro1234567`` and ``1234567`` are the same tax code: letters and digits
    only, upper case, without a two-letter country prefix."""
    vat = "".join(ch for ch in (vat or "") if ch.isalnum()).upper()
    if len(vat) > 2 and vat[:2].isalpha():
        vat = vat[2:]
    return vat


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
