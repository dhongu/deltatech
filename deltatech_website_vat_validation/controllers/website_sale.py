# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import re

from odoo import _
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale

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
                        _("Pentru România, numele companiei este obligatoriu și trebuie să aibă cel puțin 3 caractere.")
                    )
                elif re.match(r"^[-._\s]+$", company_name):
                    error["company_name"] = "error"
                    error_message.append(_("Vă rugăm introduceți numele complet al companiei (ex: SC EXAMPLE SRL)."))

                # Validare CUI obligatoriu
                if not vat:
                    error["vat"] = "error"
                    error_message.append(_("Pentru România, CUI-ul este obligatoriu pentru persoane juridice."))
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
        for field, (value, domain_field) in duplicates_fields.items():
            if value and field not in error:
                domain = [(domain_field, "=", value), ("id", "!=", partner.id)]
                partner_exists = request.env["res.partner"].search(domain, limit=1)
                if partner_exists:
                    error[field] = "error"
                    if field == "vat":
                        error_message.append(_("Un alt partener există deja cu CUI-ul %s") % value)
                    elif field == "email":
                        error_message.append(_("Un alt partener există deja cu emailul %s") % value)
                    elif field == "phone":
                        error_message.append(_("Un alt partener există deja cu telefonul %s") % value)

        return error, error_message
