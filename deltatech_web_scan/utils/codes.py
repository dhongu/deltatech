# Part of Terrabit. See LICENSE file for full copyright and licensing details.
"""Prices and codes read from web pages: prices written the Romanian or the English way, product codes
compared without their punctuation, and barcodes (GTIN-8, UPC-A, EAN-13, GTIN-14) with their GS1 check digit."""

import re

GTIN_LENGTHS = (8, 12, 13, 14)
CODE_PUNCTUATION_RE = re.compile(r"[\s\-./_]+")
NUMBER_RE = re.compile(r"\d[\d\s.,'  ]*")


def _parse_number(text, structured):
    text = re.sub(r"[\s'  ]", "", text).rstrip(".,")
    if not text:
        return None
    if "," in text and "." in text:
        # both separators: the rightmost one is the decimal separator
        decimal, thousands = (",", ".") if text.rfind(",") > text.rfind(".") else (".", ",")
        text = text.replace(thousands, "").replace(decimal, ".")
    elif "," in text or "." in text:
        sep = "," if "," in text else "."
        parts = text.split(sep)
        if structured and sep == ".":
            # schema.org asks for a dot as decimal separator
            text = text if len(parts) == 2 else text.replace(".", "")
        elif len(parts) > 2 or len(parts[1]) == 3:
            # 1.299.000 or 1.299 / 1,299: a separator followed by 3 digits groups the thousands
            text = text.replace(sep, "")
        else:
            text = text.replace(sep, ".")
    try:
        return float(text)
    except ValueError:
        return None


def parse_price(value, structured=False):
    """:return: the price written in a value, as a float, or None

    ``structured`` is set for the values of schema.org data (JSON-LD, Microdata), where a dot is
    always the decimal separator; elsewhere a separator followed by exactly 3 digits groups the
    thousands (``1.299`` and ``1,299`` are 1299), as the prices of the shops have 2 decimals.
    """
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value) if value >= 0 else None
    match = NUMBER_RE.search(str(value))
    return _parse_number(match.group(0), structured) if match else None


def normalize_code(code, strip_zeros=False):
    """:return: the code in capitals, without spaces, dashes, dots, slashes and underscores
    (and without leading zeros, when asked), to compare the codes of two catalogues"""
    code = CODE_PUNCTUATION_RE.sub("", str(code or "")).upper()
    return code.lstrip("0") if strip_zeros else code


def same_code(code1, code2, strip_zeros=False):
    """:return: True when both codes are the same once normalized"""
    code1, code2 = normalize_code(code1, strip_zeros), normalize_code(code2, strip_zeros)
    return bool(code1) and code1 == code2


def normalize_gtin(code):
    """:return: the digits of the code, or an empty text when it is not made of digits, spaces and dashes"""
    code = str(code or "").strip()
    if not code or not re.fullmatch(r"[\d\s-]+", code):
        return ""
    return re.sub(r"\D", "", code)


def is_valid_gtin(code):
    """:return: True when the code has the length of a GTIN and the right GS1 check digit"""
    if len(code or "") not in GTIN_LENGTHS or not code.isdigit():
        return False
    digits = [int(d) for d in code]
    # from the right, without the check digit: weights 3, 1, 3, 1...
    total = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(digits[:-1])))
    return (10 - total % 10) % 10 == digits[-1]


def same_gtin(code1, code2):
    """:return: True when both codes are the same GTIN, written with or without leading zeros"""
    code1, code2 = normalize_gtin(code1), normalize_gtin(code2)
    return bool(code1 and code2) and code1.zfill(14) == code2.zfill(14)
