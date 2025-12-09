# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# Vezi fisierul README.rst din radacina addon-ului pentru detalii despre licenta

import re

from odoo import _, http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.tools import email_normalize

from .vat_utils import (
    normalize_email,
    normalize_phone,
    normalize_vat,
    validate_email,
    validate_phone,
    validate_vat,
)


class WebsiteSaleVATValidation(WebsiteSale):
    def checkout_form_validate(self, mode, all_form_values, data):
        """
        Extinde validarea formularului de checkout pentru:
        - Validare duplicate VAT/email/phone
        - Validare obligatorie CUI pentru România
        - Validare format CUI românesc
        - Validare nume companie pentru România
        """
        error = dict()
        error_message = []

        # Obține țara selectată
        country = None
        country_raw = data.get("country_id")
        if country_raw:
            country_id_str = str(country_raw).strip()
            if country_id_str.isdigit():
                country = request.env["res.country"].browse(int(country_id_str))

        # Curăță spațiile din câmpuri
        for field in ["vat", "email", "phone"]:
            if field in data and data.get(field):
                data[field] = data.get(field).strip()

        # Normalizează VAT-ul (uppercase, fără spații și prefix RO dacă lipsă)
        if "vat" in data and data.get("vat"):
            data["vat"] = normalize_vat(data["vat"], country)

        # Apelează validarea standard
        standard_error, standard_error_message = super().checkout_form_validate(mode, all_form_values, data)

        error.update(standard_error)
        error_message += standard_error_message
        partner = request.env["res.users"].browse(request.uid).partner_id

        # Validări specifice pentru România
        if country and country.code == "RO":
            # Verifică dacă sunt completate câmpurile B2B (show_vat)
            company_name = data.get("company_name", "").strip()
            vat = data.get("vat", "").strip()

            # Dacă utilizatorul completează oricare din câmpurile de companie, le cerem pe amândouă
            if company_name or vat:
                # Validare nume companie
                if not company_name or len(company_name) < 3:
                    error["company_name"] = "error"
                    error_message.append(
                        _("For Romania, the company name is required and must have at least 3 characters.")
                    )
                elif re.match(r"^[-._\s]+$", company_name):
                    error["company_name"] = "error"
                    error_message.append(_("Please enter the full legal company name (e.g., SC EXAMPLE SRL)."))

                # Validare CUI obligatoriu
                if not vat:
                    error["vat"] = "error"
                    error_message.append(_("For Romania, the VAT number is mandatory for companies."))
                else:
                    # Validare format CUI
                    vat_error = validate_vat(vat, country)
                    if vat_error:
                        error["vat"] = "error"
                        error_message.append(vat_error)

        # Validare email
        email_normalized, email_error = ("", False)
        if "email" not in error:
            email_normalized, email_error = validate_email(data.get("email"))
            if email_error:
                error["email"] = "error"
                error_message.append(email_error)
        if email_normalized:
            data["email"] = email_normalized

        # Validare telefon
        phone_normalized, phone_error = ("", False)
        if "phone" not in error:
            phone_normalized, phone_error = validate_phone(data.get("phone"), country)
            if phone_error:
                error["phone"] = "error"
                error_message.append(phone_error)
        if phone_normalized:
            data["phone"] = phone_normalized

        # Normalizează pentru verificare duplicate
        vat_normalized = normalize_vat(data.get("vat"), country)
        email_for_dup = email_normalized or normalize_email(data.get("email"))
        phone_for_dup = phone_normalized or normalize_phone(data.get("phone"))

        duplicates_fields = {
            "vat": (vat_normalized, "vat"),
            "email": (email_for_dup, "email_normalized"),
            "phone": (phone_for_dup, "phone_sanitized"),
        }

        # Validare duplicate pentru VAT, email, phone (pe toți partenerii, nu doar top-level)
        partner_model = request.env["res.partner"].sudo()
        for field, (value, domain_field) in duplicates_fields.items():
            if value and field not in error:
                domain = [(domain_field, "=", value), ("id", "!=", partner.id)]
                partner_exists = partner_model.search(domain, limit=1)
                if partner_exists:
                    error[field] = "error"
                    if field == "vat":
                        error_message.append(_("Another partner already exists with the VAT number %s.") % value)
                    elif field == "email":
                        error_message.append(_("Another partner already exists with the email %s.") % value)
                    elif field == "phone":
                        error_message.append(_("Another partner already exists with the phone number %s.") % value)

        return error, error_message

    # ------------------------------------------------------------------
    # Address form (anonymous checkout): enforce duplicate check too
    # ------------------------------------------------------------------
    def _validate_address_values(
        self,
        address_values,
        partner_sudo,
        address_type,
        use_delivery_as_billing,
        required_fields,
        is_main_address,
        **kwargs,
    ):
        """Extend standard validation to block duplicate partners in anonymous checkout."""
        invalid_fields, missing_fields, error_messages = super()._validate_address_values(
            address_values,
            partner_sudo,
            address_type,
            use_delivery_as_billing,
            required_fields,
            is_main_address,
            **kwargs,
        )

        # Only check duplicates when creating a new main address (anonymous cart).
        if partner_sudo:
            return invalid_fields, missing_fields, error_messages

        country = None
        if address_values.get("country_id"):
            country = request.env["res.country"].browse(int(address_values["country_id"]))

        vat_val = normalize_vat(address_values.get("vat"), country)
        email_val = normalize_email(address_values.get("email"))

        phone_val = ""
        if address_values.get("phone"):
            phone_normalized, phone_error = validate_phone(address_values.get("phone"), country)
            if phone_error:
                invalid_fields.add("phone")
                error_messages.append(phone_error)
            phone_val = phone_normalized

        duplicate_found = False
        partner_model = request.env["res.partner"].sudo().with_context(active_test=False)

        # VAT duplicate
        if vat_val and "vat" not in invalid_fields:
            dup = partner_model.search([("vat", "=", vat_val)], limit=1)
            if dup:
                invalid_fields.add("vat")
                duplicate_found = True

        # Email duplicate (try normalized + raw)
        if email_val and "email" not in invalid_fields:
            dup_email = partner_model.search(
                ["|", ("email_normalized", "=", email_val), ("email", "=", address_values.get("email"))],
                limit=1,
            )
            if dup_email:
                invalid_fields.add("email")
                duplicate_found = True

        # Phone duplicate (try sanitized + raw)
        if phone_val and "phone" not in invalid_fields:
            dup_phone = partner_model.search(
                ["|", ("phone_sanitized", "=", phone_val), ("phone", "=", address_values.get("phone"))],
                limit=1,
            )
            if dup_phone:
                invalid_fields.add("phone")
                duplicate_found = True

        if duplicate_found:
            generic_msg = _("An account with these details already exists. Please sign in or request an access link.")
            if generic_msg not in error_messages:
                error_messages.append(generic_msg)

        return invalid_fields, missing_fields, error_messages

    # ------------------------------------------------------------------
    # Send portal access / reset link for existing partner
    # ------------------------------------------------------------------
    @http.route(
        "/shop/send_portal_access",
        type="json",
        auth="public",
        website=True,
        methods=["POST"],
    )
    def send_portal_access(self, email=None, **_kwargs):
        email_norm = email_normalize(email or "")
        if not email_norm:
            return {"success": False, "message": _("Please enter a valid email.")}

        partner = (
            request.env["res.partner"]
            .sudo()
            .with_context(active_test=False)
            .search(
                [
                    "|",
                    ("email_normalized", "=", email_norm),
                    ("email", "=", email),
                ],
                limit=1,
            )
        )
        if not partner:
            return {"success": False, "message": _("No customer found with this email.")}

        user = (
            partner.user_ids.filtered(lambda u: u.share)[:1]
            or request.env["res.users"].sudo().search([("login", "=", email_norm)], limit=1)
        )

        if not user:
            group_portal = request.env.ref("base.group_portal")
            user = request.env["res.users"].sudo().create(
                {
                    "name": partner.name or email_norm,
                    "login": email_norm,
                    "email": email_norm,
                    "partner_id": partner.id,
                    "groups_id": [(6, 0, [group_portal.id])],
                }
            )

        # Trimite emailul standard de reset/parolă
        try:
            user.action_reset_password()
        except Exception as exc:
            return {"success": False, "message": _("Could not send the access email: %s") % exc}

        return {
            "success": True,
            "message": _("We sent an access link to %s. Please check your inbox/spam.") % email_norm,
        }
