# ¶¸  2008-2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com>
# Vezi fisierul README.rst din radacina addon-ului pentru detalii despre licenta

import re

from odoo import _
from odoo.exceptions import UserError
from odoo.tools import email_normalize

from odoo.addons.phone_validation.tools import phone_validation


def normalize_vat(vat, country=None):
    """Normalizeaza CUI-ul prin eliminarea spatiilor, transformarea in majuscule si adaugarea prefixului RO daca lipseste."""
    if not vat:
        return ""

    normalized = vat.strip().upper().replace(" ", "")

    if country and country.code == "RO":
        # Acceptam siruri formate din cifre si adaugam prefixul RO
        if normalized.isdigit():
            normalized = f"RO{normalized}"
        elif normalized.startswith("RO"):
            normalized = f"RO{normalized[2:]}"

    return normalized


def validate_vat(vat, country=None):
    """Returneaza mesaj de eroare daca CUI-ul este invalid pentru tara primita, altfel False."""
    if not vat:
        return False

    if country and country.code == "RO":
        return _validate_romanian_vat(vat)

    return False


def _validate_romanian_vat(vat):
    """Valideaza formatul si cifra de control pentru CUI-ul romanesc."""
    vat = vat.strip().upper()

    if vat.startswith("RO"):
        number = vat[2:]
    else:
        number = vat

    if not number.isdigit():
        return _(
            "The VAT number must contain digits only after the optional RO prefix. Example: 12345678 or RO12345678."
        )

    if len(number) < 2 or len(number) > 10:
        return _("The VAT number must have between 2 and 10 digits.")

    base, check_digit = number[:-1], int(number[-1])
    factors = [7, 5, 3, 2, 1, 7, 5, 3, 2]
    padded = base.zfill(len(factors))
    total = sum(int(digit) * factor for digit, factor in zip(padded, factors))
    remainder = total % 11
    computed = 0 if remainder == 10 else remainder

    if computed != check_digit:
        return _("Invalid VAT number: the checksum digit does not match.")

    # Interzicem caractere speciale suplimentare fata de cifre
    if re.search(r"[^0-9]", number):
        return _("The VAT number must contain digits only.")

    return False


def normalize_email(email):
    """Normalizeaza email-ul prin utilizarea helper-ului Odoo."""
    if not email:
        return ""
    return email_normalize(email) or ""


def normalize_phone(phone):
    """Normalizeaza telefonul prin eliminarea simbolurilor evidente."""
    if not phone:
        return ""
    phone_clean = re.sub(r"[\\s().-]", "", phone)
    if phone_clean.startswith("00"):
        phone_clean = f"+{phone_clean[2:]}"
    return phone_clean


def validate_email(email):
    """Returneaza (email_normalizat, mesaj_de_eroare)."""
    if not email:
        return "", False
    normalized = email_normalize(email)
    if not normalized:
        return "", _("The email address is not valid.")
    return normalized, False


def validate_phone(phone, country=None):
    """Returneaza (telefon_normalizat, mesaj_de_eroare)."""
    if not phone:
        return "", False

    country_code = country.code if country else None
    country_phone_code = country.phone_code if country else None

    try:
        sanitized = phone_validation.phone_format(
            phone,
            country_code,
            country_phone_code,
            force_format="E164",
            raise_exception=True,
        )
    except UserError:
        sanitized = False

    if not sanitized:
        return "", _("The phone number is not valid.")
    return sanitized, False
