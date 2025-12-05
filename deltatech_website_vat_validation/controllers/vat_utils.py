# ©  2008-2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

import re

from odoo import _
from odoo.addons.phone_validation.tools import phone_validation
from odoo.exceptions import UserError
from odoo.tools import email_normalize


def normalize_vat(vat, country=None):
    """Normalize VAT by trimming spaces, uppercasing and adding RO prefix when missing."""
    if not vat:
        return ""

    normalized = vat.strip().upper().replace(" ", "")

    if country and country.code == "RO":
        # Accept bare digits by prefixing RO
        if normalized.isdigit():
            normalized = f"RO{normalized}"
        elif normalized.startswith("RO"):
            normalized = f"RO{normalized[2:]}"

    return normalized


def validate_vat(vat, country=None):
    """Return error message if VAT is invalid for the given country, otherwise False."""
    if not vat:
        return False

    if country and country.code == "RO":
        return _validate_romanian_vat(vat)

    return False


def _validate_romanian_vat(vat):
    """Validate Romanian CUI format + checksum."""
    vat = vat.strip().upper()

    if vat.startswith("RO"):
        number = vat[2:]
    else:
        number = vat

    if not number.isdigit():
        return _(
            "CUI-ul trebuie să conțină doar cifre după prefixul RO (opțional). "
            "Format corect: 12345678 sau RO12345678"
        )

    if len(number) < 2 or len(number) > 10:
        return _("CUI-ul trebuie să aibă între 2 și 10 cifre.")

    base, check_digit = number[:-1], int(number[-1])
    factors = [7, 5, 3, 2, 1, 7, 5, 3, 2]
    padded = base.zfill(len(factors))
    total = sum(int(digit) * factor for digit, factor in zip(padded, factors))
    remainder = total % 11
    computed = 0 if remainder == 10 else remainder

    if computed != check_digit:
        return _("CUI invalid: cifra de control nu corespunde.")

    # Forbid special chars (defensive, though digits check above covers most)
    if re.search(r"[^0-9]", number):
        return _("CUI-ul trebuie să conțină doar cifre.")

    return False


def normalize_email(email):
    if not email:
        return ""
    return email_normalize(email) or ""


def normalize_phone(phone):
    if not phone:
        return ""
    phone_clean = re.sub(r"[\\s().-]", "", phone)
    if phone_clean.startswith("00"):
        phone_clean = f"+{phone_clean[2:]}"
    return phone_clean


def validate_email(email):
    """Return (normalized_email, error_message)."""
    if not email:
        return "", False
    normalized = email_normalize(email)
    if not normalized:
        return "", _("Adresa de email nu este validă.")
    return normalized, False


def validate_phone(phone, country=None):
    """Return (sanitized_phone, error_message)."""
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
        return "", _("Numărul de telefon nu este valid.")
    return sanitized, False
