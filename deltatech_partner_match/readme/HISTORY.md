## 19.0.1.0.1 (2026-10-23)

- The legal forms "SAS", "AG", "BV", "NV" and "RA" are no longer dropped from the names: on a database of 551,000 partners they removed the surname Sas ("Sas Vasile" became "vasile") and initials ("INSTALCO A.G. SRL", "BO & RA TRANS SRL"). KFT, SARL, s.r.o., SPRL and CMI stay.

## 19.0.1.0.0 (2026-10-23)

- Add: shared normalization and fuzzy matching of partners (name, VAT, phone, email), and
  `res.partner._find_similar_partners`, which selects candidates on the VAT number, the email or the
  phone and scores them, without deciding anything. One list of legal forms (Romania and EU), the
  phone rule of Odoo's `phone_validation` (possible and valid number), the CUI / CNP / EU VAT check
  with `python-stdnum`. `phonenumbers`, `rapidfuzz` and `unidecode` are optional.
- Installed with `deltatech_partner_merge` and `deltatech_marketplace` once they use it: an accepted
  exception to the rule of no new dependency on modules installed at customers, since this module
  adds no fields, data, scheduled actions or record rules and changes no behavior by itself.
