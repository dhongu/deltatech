# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# Vezi fisierul README.rst din radacina addon-ului pentru detalii despre licenta

import re

from odoo import _
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal

from .vat_utils import (
    normalize_email,
    normalize_phone,
    normalize_vat,
    validate_email,
    validate_phone,
    validate_vat,
)


class CustomerPortalVATValidation(CustomerPortal):
    def details_form_validate(self, data, partner_creation=False):
        """
        Extinde validarea formularului de portal pentru:
        - Validare duplicate VAT/email/phone
        - Validare obligatorie CUI pentru România
        - Validare format CUI românesc
        - Validare nume companie pentru România
        """
        partner = request.env["res.users"].browse(request.uid).partner_id

        # Curăță spațiile din câmpuri
        for field in ["vat", "email", "phone"]:
            if field in data and data.get(field):
                data[field] = data.get(field).strip()

        # Obține țara selectată
        country_raw = data.get("country_id")
        if country_raw:
            country_id_str = str(country_raw).strip()
            if country_id_str.isdigit():
                country = request.env["res.country"].browse(int(country_id_str))
            else:
                country = partner.country_id
        else:
            country = partner.country_id

        # Normalizează VAT-ul (uppercase, fără spații și prefix RO dacă lipsă)
        if "vat" in data and data.get("vat"):
            data["vat"] = normalize_vat(data["vat"], country)

        # Apelează validarea standard
        error, error_message = super().details_form_validate(data, partner_creation)

        # Validări specifice pentru România
        if country and country.code == "RO":
            company_name = data.get("company_name", "").strip()
            vat = data.get("vat", "").strip()

            # Dacă utilizatorul completează oricare din câmpurile de companie
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
