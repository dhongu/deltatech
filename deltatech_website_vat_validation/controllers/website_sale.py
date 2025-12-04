# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import re

from odoo import _
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


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

        # Curăță spațiile din câmpuri
        for field in ["vat", "email", "phone"]:
            if field in data and data.get(field):
                data[field] = data.get(field).strip()

        # Normalizează VAT-ul (uppercase, fără spații)
        if "vat" in data and data.get("vat"):
            data["vat"] = data["vat"].upper().replace(" ", "")

        # Apelează validarea standard
        standard_error, standard_error_message = super().checkout_form_validate(mode, all_form_values, data)

        error.update(standard_error)
        error_message += standard_error_message
        partner = request.env["res.users"].browse(request.uid).partner_id

        # Obține țara selectată
        country_id = data.get("country_id")
        country = request.env["res.country"].browse(int(country_id)) if country_id else None

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
                    vat_error = self._validate_romanian_vat_format(vat)
                    if vat_error:
                        error["vat"] = "error"
                        error_message.append(vat_error)

        # Validare duplicate pentru VAT, email, phone
        for field in ["vat", "email", "phone"]:
            value = data.get(field, False)
            if value and field not in error:
                domain = [(field, "=", value), ("id", "!=", partner.id), ("parent_id", "=", False)]
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

    def _validate_romanian_vat_format(self, vat):
        """
        Validează formatul CUI-ului românesc

        Args:
            vat (str): CUI-ul de validat

        Returns:
            str or False: Mesaj de eroare sau False dacă validarea reușește
        """
        if not vat:
            return False

        # Verifică caractere invalide (-, ., _, etc.)
        invalid_chars = re.compile(r"[-._,;:!@#$%^&*()+={}\[\]|\\<>?\/~`'\"]")
        if invalid_chars.search(vat):
            return _(
                "CUI-ul nu poate conține caractere speciale (-, ., _, etc.). "
                "Introduceți doar cifre sau RO urmat de cifre."
            )

        # Elimină prefixul RO dacă există
        vat_number = vat.replace("RO", "")

        # Verifică dacă sunt doar cifre
        if not vat_number.isdigit():
            return _(
                "CUI-ul trebuie să conțină doar cifre după prefixul RO (opțional). "
                "Format corect: 12345678 sau RO12345678"
            )

        # Verifică lungimea (CUI românesc are între 2 și 10 cifre)
        if len(vat_number) < 2 or len(vat_number) > 10:
            return _("CUI-ul trebuie să aibă între 2 și 10 cifre.")

        # Validare reușită
        return False
