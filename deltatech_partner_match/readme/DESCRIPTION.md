Technical module: one place for the rules that decide whether two partner records are the same,
so the modules that look for an existing partner (marketplace import, duplicate finder, trial
balance import) recognize the same partner the same way.

It adds no fields, data, menus, scheduled actions or record rules, and changes no behavior by
itself: it only provides functions that other modules call.

**Normalization** (`deltatech_partner_match.tools.partner_match`, plain Python):

- **Name**: lowercase, without diacritics, punctuation and legal forms (one list for Romania and
  the EU: SRL, SA, PFA, II, GmbH, Ltd, SARL, KFT...), words sorted. "S.C. Popescu Ion S.R.L." and
  "ion popescu srl" give the same key.
- **VAT**: alphanumerics only, without the country prefix and the leading zeros ("RO 012.345" =
  "12345"); the check digit of a Romanian CUI or CNP, or of an EU VAT number, with `python-stdnum`.
- **Phone**: E.164 (`+40722123456`) with the same rule Odoo uses for `phone_sanitized` (a possible
  and valid number, with `phonenumbers`); without the library, the Romanian formats and the numbers
  written with an international prefix. For bulk comparison, the last nine digits.
- **Email**: Odoo's own `email_normalize`.

**Matching**:

- `name_similarity` (0-1) pairs every word with the closest word of the other name, so a shared
  surname alone does not make two people alike: use it to decide whether two records are the same
  partner.
- `token_sort_ratio` and `similar_pairs` (0-100) compare whole names, in bulk; `rapidfuzz` is used
  when installed, `difflib` otherwise, on limited blocks. Use them to propose pairs for review.
- `res.partner._find_similar_partners(values, domain, keys, limit)` selects the partners that share
  the VAT number, the email or the phone of `values` (never a name alone), and returns them with a
  score and the keys they share. When both sides name a different county, the street and
  the city do not count: the same village name exists in several counties. Whether one is reused is decided by the calling module.

`phonenumbers`, `rapidfuzz` and `unidecode` are optional: the results stay the same without them on
the exact keys, and slightly coarser on the phones of other countries.
