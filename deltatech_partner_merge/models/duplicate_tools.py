# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
"""Normalization and matching used by the duplicate finder.

Plain Python, no ORM: the scan loads the partners with one query and works on tuples, so tens of
thousands of records fit in memory. The optional libraries are only accelerators — without them the
results are the same on the exact keys and slightly slower (and capped per block) on the names.
"""

import contextlib
import difflib
import re
import unicodedata

from odoo.tools import email_normalize

try:
    import phonenumbers
except ImportError:  # pragma: no cover - depends on the server
    phonenumbers = None

try:
    from unidecode import unidecode
except ImportError:  # pragma: no cover - depends on the server
    unidecode = None

try:
    from rapidfuzz import fuzz as rf_fuzz
    from rapidfuzz import process as rf_process
except ImportError:  # pragma: no cover - depends on the server
    rf_fuzz = rf_process = None

LEGAL_FORMS = {
    "sc",
    "srl",
    "srld",
    "sa",
    "pfa",
    "ii",
    "if",
    "snc",
    "scs",
    "sca",
    "ong",
    "ltd",
    "llc",
    "gmbh",
    "inc",
    "spa",
}
STREET_WORDS = {
    "str",
    "strada",
    "nr",
    "numar",
    "bl",
    "bloc",
    "sc",
    "scara",
    "ap",
    "apartament",
    "et",
    "etaj",
    "bd",
    "bdul",
    "blvd",
    "bulevardul",
    "calea",
    "sos",
    "soseaua",
    "aleea",
    "al",
    "piata",
    "jud",
    "judet",
    "sector",
}

# rows of a block compared at once by rapidfuzz: 1000 x n uint8 scores, a few MB per chunk
CDIST_CHUNK = 1000
# largest block the pure-Python fallback compares: n² / 2 SequenceMatcher calls
DIFFLIB_MAX_BLOCK = 1500


def has_rapidfuzz():
    return rf_process is not None


def ascii_fold(text):
    if unidecode:
        return unidecode(text)
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _tokens(text, drop=()):
    if not text:
        return []
    text = ascii_fold(text).lower().replace(".", "")
    return [token for token in re.split(r"[^a-z0-9]+", text) if token and token not in drop]


def normalize_name(name):
    """Lowercase, without diacritics, punctuation and legal forms, words sorted:
    ``"S.C. Popescu Ion S.R.L."`` and ``"ion popescu srl"`` give the same key."""
    return " ".join(sorted(_tokens(name, LEGAL_FORMS)))


def name_prefix(name):
    """First letters of the name as written (not sorted), the fallback block."""
    tokens = _tokens(name, LEGAL_FORMS)
    return tokens[0][:3] if tokens else ""


def normalize_street(street):
    return " ".join(sorted(_tokens(street, STREET_WORDS)))


def normalize_city(city):
    return " ".join(_tokens(city))


def normalize_email(email):
    if not email:
        return None
    return email_normalize(email, strict=False) or None


def normalize_vat(vat):
    """Uppercase, alphanumerics only, without the country prefix (RO123 = 123)."""
    if not vat:
        return None
    vat = re.sub(r"[^0-9A-Za-z]", "", vat).upper()
    vat = re.sub(r"^[A-Z]{2}(?=\d)", "", vat)
    return vat if len(vat) >= 4 and vat.strip("0") else None


def normalize_phone(phone, country_code=None):
    """E.164 when ``phonenumbers`` can parse the number; otherwise the last nine digits, which
    still matches the national and the international form of the same Romanian number."""
    if not phone:
        return None
    if phonenumbers:
        # unparsable numbers fall through to the digits key
        with contextlib.suppress(phonenumbers.NumberParseException):
            number = phonenumbers.parse(phone, (country_code or "").upper() or None)
            if phonenumbers.is_valid_number(number):
                return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 7 or len(set(digits)) == 1:
        return None
    return "~" + digits[-9:]


def phone_key(normalized):
    """E.164 and the digits fallback of the same number must meet: compare on the last nine digits."""
    return normalized and normalized.lstrip("~+")[-9:]


class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, item):
        parent = self.parent.setdefault(item, item)
        if parent != item:
            parent = self.parent[item] = self.find(parent)
        return parent

    def union(self, a, b):
        root_a, root_b = self.find(a), self.find(b)
        if root_a != root_b:
            self.parent[max(root_a, root_b)] = min(root_a, root_b)

    def groups(self):
        result = {}
        for item in self.parent:
            result.setdefault(self.find(item), []).append(item)
        return [sorted(members) for members in result.values() if len(members) > 1]


def similar_pairs(names, threshold):
    """Pairs (i, j, score) with i < j whose names score at least ``threshold`` (0-100).

    rapidfuzz: ``process.cdist`` with ``token_sort_ratio``, chunked so memory stays bounded.
    Fallback: difflib on the already token-sorted names, with the cheap upper bounds first.
    Returns None when the fallback refuses a block that is too large.
    """
    count = len(names)
    if count < 2:
        return []
    pairs = []
    if rf_process:
        for start in range(0, count, CDIST_CHUNK):
            chunk = names[start : start + CDIST_CHUNK]
            matrix = rf_process.cdist(
                chunk,
                names,
                scorer=rf_fuzz.token_sort_ratio,
                score_cutoff=threshold,
                dtype="uint8",
                workers=-1,
            )
            for row, cols in enumerate(matrix):
                i = start + row
                for j in cols.nonzero()[0]:
                    if j > i:
                        pairs.append((i, int(j), int(cols[j])))
        return pairs
    if count > DIFFLIB_MAX_BLOCK:
        return None
    ratio = threshold / 100.0
    matcher = difflib.SequenceMatcher(None, autojunk=False)
    for i in range(count):
        matcher.set_seq2(names[i])  # the cached side
        for j in range(i + 1, count):
            matcher.set_seq1(names[j])
            if matcher.real_quick_ratio() >= ratio and matcher.quick_ratio() >= ratio:
                score = matcher.ratio()
                if score >= ratio:
                    pairs.append((i, j, round(score * 100)))
    return pairs
