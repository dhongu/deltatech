# (c) 2008-2021 Deltatech
#         Dorin Hongu <dhongu(@)gmail(.)com
# Vezi fisierul README.rst din radacina addon-ului pentru detalii despre licenta

import logging

from odoo import _, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class AnafLookupController(http.Controller):
    """
    Controller pentru interogarea ANAF din website
    Permite auto-completarea datelor companiei pe baza CUI-ului
    """

    @http.route(
        "/shop/anaf_lookup",
        type="json",
        auth="public",
        website=True,
        methods=["POST"],
    )
    def anaf_lookup(self, vat=None, **kwargs):
        """
        Endpoint AJAX pentru cautarea datelor companiei in ANAF.
        
        Note: This endpoint is public and should be protected with rate limiting
        (e.g., using a reverse proxy like nginx limit_req or Odoo's ir.http rate limiting)
        to prevent abuse and DoS attacks. The ANAF API timeout is set in the
        l10n_ro_partner_create_by_vat module (currently 30s, recommended 10s).
        """
        result = {
            "success": False,
            "error": "",
            "data": {},
        }

        if not vat:
            result["error"] = _("The VAT number is required.")
            return result

        vat = vat.strip().upper().replace(" ", "")
        vat_number = vat.replace("RO", "")

        if not vat_number.isdigit():
            result["error"] = _("The VAT number must contain digits only.")
            return result

        if len(vat_number) < 2 or len(vat_number) > 10:
            result["error"] = _("The VAT number must have between 2 and 10 digits.")
            return result

        partner_model = request.env["res.partner"].sudo()

        try:
            anaf_error, anaf_result = partner_model._get_Anaf(vat_number)
            if anaf_error:
                result["error"] = str(anaf_error)
                return result

            if not anaf_result or not anaf_result.get("date_generale"):
                result["error"] = _("No company data was found for the VAT %s.") % vat_number
                return result

            partner_template = partner_model.new({})
            mapped_data = partner_template._Anaf_to_Odoo(anaf_result)

            if not mapped_data:
                result["error"] = _("ANAF did not return valid data for the provided VAT number.")
                return result

            response_data = self._serialize_anaf_data(mapped_data, anaf_result, vat_number)

            result["success"] = True
            result["data"] = response_data

            _logger.info(
                "ANAF lookup successful for CUI %s: %s",
                vat_number,
                response_data.get("company_name"),
            )
        except Exception as exc:
            _logger.exception("ANAF lookup error for VAT %s", vat_number)
            result["error"] = _("Could not retrieve company data from ANAF. Please try again later or enter manually.")

        return result

    def _serialize_anaf_data(self, mapped_data, anaf_result, vat_number):
        """
        Transformam rezultatele din modulul OCA pentru consumul website-ului.
        """

        def _extract_m2o(value):
            return value.id if hasattr(value, "id") else value or False

        general_data = anaf_result.get("date_generale", {})

        vat_value = (mapped_data.get("vat") or vat_number).strip()

        return {
            "company_name": (mapped_data.get("name") or "").strip(),
            "vat": vat_value,
            "street": (mapped_data.get("street") or "").strip(),
            "street2": (mapped_data.get("street2") or "").strip(),
            "city": (mapped_data.get("city") or "").strip(),
            "state_id": _extract_m2o(mapped_data.get("state_id")),
            "zip": (mapped_data.get("zip") or "").strip(),
            "phone": (mapped_data.get("phone") or "").strip(),
            "is_vat_subjected": mapped_data.get("l10n_ro_vat_subjected", False),
            "nrc": (mapped_data.get("nrc") or "").strip(),
            "status": general_data.get("stare_inregistrare", ""),
        }
