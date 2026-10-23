## 19.0.1.1.1 (2026-10-23)

- Development status *Production/Stable*: `deltatech_marketplace` (*Production/Stable*) depends on this module, and a stable module cannot depend on a *Beta* one (`manifestoo check-dev-status` in CI). The rules are those the marketplace import and the duplicate finder already use in production.

## 19.0.1.1.0 (2026-10-23)

- The county counts in the score of `_find_similar_partners`: when both sides name a county (`state_id`, or a code or name in `county` / `state_code`, as the marketplace connectors send it) and it is not the same, the street and the city score 0. A village name is shared by up to 23 counties ("Satu Nou", "Poiana", "Dumbrava": 1,411 of the 10,565 Romanian locality names), so the same street and village in another county is another address. The score can only go down: a county that matches no state, or a missing one, leaves it as before.

## 19.0.1.0.2 (2026-10-23)

- `normalize_text` and `jaccard_similarity` (street and city in `_find_similar_partners`) split the words on dots again, as the marketplace import did: "Str.Memorandumului 10" and "Str. Memorandumului 10" scored 0.25 on the street instead of 1. The name, street and city keys of the duplicate finder are unchanged.
- Apps Store banner (`banner.json`), instead of the generic screenshot.

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
