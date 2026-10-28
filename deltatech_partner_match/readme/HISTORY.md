## 19.0.1.3.0 (2026-10-28)

- The county lowers the score only when both counties have a locality of that name (`res.city`, from `base_address_extended`), as "Satu Nou" in Bacău and in Iași. On a database of 528,000 partners, 2.1% have a county that does not fit their city ("Sibiu" in Timiș, București in 25 counties): with the rule of 19.0.1.1.0 these lost the street and city points against a correct import, so the marketplace created a new contact instead of reusing them. A county that does not fit the city is now ignored, and without the list of localities the county never lowers the score.

## 19.0.1.2.0 (2026-10-24)

- Add `name_words`: the name without diacritics, punctuation and legal forms, with the words in their order, for an exact name key where the order matters ("Alfa Beta" and "Beta Alfa" can be two companies). `normalize_name` is the same with the words sorted. Used by the trial balance import.

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
