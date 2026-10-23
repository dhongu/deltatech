## 19.0.1.0.0 (2026-10-23)

- Add: shared normalization and fuzzy matching of partners (name, VAT, phone, email), and
  `res.partner._find_similar_partners`, which selects candidates on the VAT number, the email or the
  phone and scores them, without deciding anything. One list of legal forms (Romania and EU), the
  phone rule of Odoo's `phone_validation` (possible and valid number), the CUI / CNP / EU VAT check
  with `python-stdnum`. `phonenumbers`, `rapidfuzz` and `unidecode` are optional.
- Installed with `deltatech_partner_merge` and `deltatech_marketplace` once they use it: an accepted
  exception to the rule of no new dependency on modules installed at customers, since this module
  adds no fields, data, scheduled actions or record rules and changes no behavior by itself.
