# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
"""Normalization and matching of partners, shared by the modules that look for the same partner.

Plain Python, no ORM. The optional libraries are only accelerators or refinements: without
``phonenumbers`` the Romanian formats are still recognized, without ``unidecode`` the diacritics are
folded with ``unicodedata``, and without ``rapidfuzz`` the names are compared with ``difflib``.

Two name scores on purpose:

- :func:`name_similarity` pairs every word with the closest word of the other name, so a shared
  surname alone does not make two people alike ("Ana Popescu" / "Ion Popescu" = 0.67). Use it to
  decide whether two records are the same partner.
- :func:`token_sort_ratio` / :func:`similar_pairs` compare the whole sorted names; cheap enough to
  run on every pair of a block, but "Ana Popescu" / "Ion Popescu" scores 82. Use it to propose
  pairs that a user reviews, not to reuse a record automatically.
"""

import contextlib
import difflib
import re
import unicodedata

from stdnum.eu import vat as eu_vat
from stdnum.ro import cnp, cui

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

# legal forms dropped from the names, Romanian and the usual EU ones. Left out on purpose, since
# they are also surnames or initials: "sas" (Sas Vasile), "ag" (A.G.), "bv", "nv", "ra" (Bo & Ra)
LEGAL_FORMS = {
    # Romania
    "sc",
    "srl",
    "srld",
    "sa",
    "sca",
    "snc",
    "scs",
    "pfa",
    "ii",
    "if",
    "cmi",
    "ong",
    # EU and others
    "gmbh",
    "inc",
    "kft",
    "llc",
    "ltd",
    "sarl",
    "spa",
    "sprl",
    "sro",
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


def _tokens(text, drop=(), join_dots=True):
    """Lowercase ASCII words of ``text``. With ``join_dots`` the dots are removed before splitting,
    so the abbreviations stay one word ("S.R.L." = "srl"); without it a dot separates words, as in
    the addresses typed without a space ("Str.Lalelelor")."""
    if not text:
        return []
    text = ascii_fold(str(text)).lower()
    if join_dots:
        text = text.replace(".", "")
    return [token for token in re.split(r"[^a-z0-9]+", text) if token and token not in drop]


def normalize_text(value):
    """Lowercase ASCII words of ``value``, in their order, any punctuation (dots included) being a
    separator: "Str.Memorandumului 10" and "Str. Memorandumului 10" give the same words."""
    return " ".join(_tokens(value, join_dots=False))


def normalize_name(name):
    """Lowercase, without diacritics, punctuation and legal forms, words sorted:
    ``"S.C. Popescu Ion S.R.L."`` and ``"ion popescu srl"`` give the same key."""
    return " ".join(sorted(_tokens(name, LEGAL_FORMS)))


def name_prefix(name):
    """First letters of the name as written (not sorted), a cheap block key."""
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
    """Uppercase, alphanumerics only, without the country prefix and the leading zeros:
    ``"RO 012.345"``, ``"12345"`` and ``"ro12345"`` give ``"12345"``. None when nothing is left
    or the code is shorter than four characters."""
    if not vat:
        return None
    vat = re.sub(r"[^0-9A-Za-z]", "", str(vat)).upper()
    vat = re.sub(r"^[A-Z]{2}(?=\d)", "", vat).lstrip("0")
    return vat if len(vat) >= 4 else None


def check_vat(vat, country_code="RO"):
    """True / False for a fiscal code that passes / fails its check digit, None when it
    cannot be checked (empty, outside the EU). Without a country prefix the code is of
    ``country_code``: a Romanian CUI, or a CNP of 13 digits."""
    value = re.sub(r"[^0-9A-Z]", "", (vat or "").upper())
    if not value.strip("0"):
        return None
    prefix = re.match(r"[A-Z]{2}", value)
    if prefix and prefix.group() != "RO":
        if prefix.group().lower() in eu_vat.MEMBER_STATES | {"el"}:
            return eu_vat.is_valid(value)
        return None
    number = value[2:] if prefix else value
    if not prefix and (country_code or "").upper() != "RO":
        return None
    if not number.isdigit():
        return False
    if len(number) == 13:
        return cnp.is_valid(number)
    return cui.is_valid(number)


def normalize_phone(phone, country_code="RO"):
    """``phone`` in E.164 form (``+40722123456``), or None.

    With ``phonenumbers`` a number is formatted when it is possible and valid, the rule of
    ``phone_validation`` that fills ``phone_sanitized``, so the result can be compared with it.
    Otherwise (no library, or a number it refuses) plain rules: a number written with an
    international prefix, and the Romanian formats ``0722 123 456``, ``0040722123456``,
    ``40722123456``, ``722123456``.
    """
    if not phone:
        return None
    raw = str(phone).strip()
    country_code = (country_code or "RO").upper()
    if phonenumbers:
        # unparsable numbers fall through to the plain rules
        with contextlib.suppress(phonenumbers.NumberParseException):
            parsed = phonenumbers.parse(raw, country_code)
            if phonenumbers.is_possible_number(parsed) and phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    digits = re.sub(r"\D", "", raw)
    if raw.startswith("+"):
        return f"+{digits}" if len(digits) >= 8 else None
    if digits.startswith("00"):
        return f"+{digits[2:]}" if len(digits) >= 10 else None
    if country_code == "RO":
        if len(digits) == 11 and digits.startswith("40"):
            return f"+{digits}"
        if len(digits) == 10 and digits.startswith("0"):
            return f"+40{digits[1:]}"
        if len(digits) == 9 and digits[0] in "237":
            return f"+40{digits}"
    return None


def phone_key(phone, country_code="RO"):
    """Last nine digits of the number, the key that compares phones in bulk or when the database
    has no ``phone_sanitized``: the national and the international form of the same number meet.
    A number :func:`normalize_phone` refuses still gets a key from its digits, unless it is too
    short or a placeholder of one repeated digit."""
    normalized = normalize_phone(phone, country_code)
    digits = re.sub(r"\D", "", normalized or str(phone or ""))
    if len(digits) < 7 or len(set(digits)) == 1:
        return None
    return digits[-9:]


def jaccard_similarity(text1, text2):
    """Share (0..1) of the words common to the two texts, after :func:`normalize_text`."""
    set1, set2 = set(normalize_text(text1).split()), set(normalize_text(text2).split())
    union = len(set1 | set2)
    return len(set1 & set2) / union if union else 0.0


def name_similarity(name1, name2):
    """Similarity (0..1) of two names, whatever the order of their words.

    Every word is paired with the closest word of the other name and the ratios are averaged,
    so a shared surname alone does not make two people alike: "Ana Popescu" / "Ion Popescu"
    scores 0.67, "Popescu Ion" / "Ion Popescu" 1.
    """
    words1, words2 = normalize_name(name1).split(), normalize_name(name2).split()
    if not words1 or not words2:
        return 0.0

    def closest(word, others):
        return max(difflib.SequenceMatcher(None, word, other).ratio() for other in others)

    ratios = [closest(word, words2) for word in words1] + [closest(word, words1) for word in words2]
    return sum(ratios) / len(ratios)


def token_sort_ratio(name1, name2):
    """Similarity (0..100) of the two names with their words sorted, as ``rapidfuzz`` computes it."""
    key1, key2 = normalize_name(name1), normalize_name(name2)
    if not key1 or not key2:
        return 0
    if rf_fuzz:
        return round(rf_fuzz.ratio(key1, key2))
    return round(difflib.SequenceMatcher(None, key1, key2, autojunk=False).ratio() * 100)


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

    ``names`` are already normalized (:func:`normalize_name`). rapidfuzz: ``process.cdist`` with
    ``token_sort_ratio``, chunked so memory stays bounded. Fallback: difflib on the token-sorted
    names, with the cheap upper bounds first. Returns None when the fallback refuses a block that
    is too large.
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
