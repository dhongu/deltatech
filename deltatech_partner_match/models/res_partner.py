# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, models
from odoo.tools import SQL

from ..tools import partner_match as pm

# weights of the fields that score a candidate; the weights of the fields missing on
# either side are spread over the others
MATCH_WEIGHTS = {"name": 0.6, "street": 0.25, "city": 0.15}
MATCH_KEYS = ("vat", "email", "phone")


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _partner_match_stored(self, field_name):
        """True when ``field_name`` is a stored column of res_partner (``phone_sanitized`` comes
        with phone_validation, ``email_normalized`` with mail)."""
        field = self._fields.get(field_name)
        return bool(field and field.store)

    @api.model
    def _partner_match_keys(self, values):
        """The strong keys of ``values``: ``{"vat": ..., "email": ..., "phone": ...}``, falsy when missing."""
        country = values.get("country_code") or "RO"
        return {
            "vat": pm.normalize_vat(values.get("vat")),
            "email": pm.normalize_email(values.get("email")),
            "phone": pm.normalize_phone(values.get("phone"), country),
            "phone_key": pm.phone_key(values.get("phone"), country),
        }

    @api.model
    def _partner_match_conditions(self, keys, use):
        conditions = []
        if "vat" in use and keys["vat"]:
            conditions.append(
                SQL(
                    r"ltrim(regexp_replace(regexp_replace(upper(vat), '[^0-9A-Z]', '', 'g'), "
                    r"'^[A-Z]{2}(?=[0-9])', ''), '0') = %s",
                    keys["vat"],
                )
            )
        if "email" in use and keys["email"]:
            if self._partner_match_stored("email_normalized"):
                conditions.append(SQL("email_normalized = %s", keys["email"]))
            else:
                conditions.append(SQL("lower(trim(email)) = %s", keys["email"]))
        if "phone" in use and keys["phone_key"]:
            if keys["phone"] and self._partner_match_stored("phone_sanitized"):
                conditions.append(SQL("phone_sanitized = %s", keys["phone"]))
            else:
                # without phone_validation the stored phones keep the format they were
                # typed in: compare the national significant digits
                conditions.append(SQL(r"right(regexp_replace(phone, '\D', '', 'g'), 9) = %s", keys["phone_key"]))
        return conditions

    @api.model
    def _partner_match_states(self, values):
        """The counties (``res.country.state``) named in ``values``: ``state_id``, or the code or
        the name sent as ``county`` / ``state_code`` ("BC", "Bacău"). Empty when none is given or
        the text matches no county, so an unknown value never lowers a score."""
        states = self.env["res.country.state"]
        if values.get("state_id"):
            return states.browse(values["state_id"]).exists()
        county = (values.get("county") or values.get("state_code") or "").strip()
        if not county:
            return states
        domain = ["|", ("code", "=ilike", county), ("name", "=ilike", county)]
        if values.get("country_code"):
            domain += [("country_id.code", "=ilike", values["country_code"])]
        return states.search(domain)

    @api.model
    def _partner_match_is_locality(self, city, states):
        """True when ``city`` is the name of a locality (``res.city``, from base_address_extended) of
        one of ``states``, diacritics and punctuation ignored. False without the model."""
        if not city or not states or "res.city" not in self.env:
            return False
        key = pm.normalize_city(city)
        cities = self.env["res.city"].sudo().search_read([("state_id", "in", states.ids)], ["name"])
        return any(pm.normalize_city(locality["name"]) == key for locality in cities)

    @api.model
    def _partner_match_other_county(self, partner, values):
        """True when ``partner`` and ``values`` are in two counties that both have a locality of
        that name ("Satu Nou" in Bacău and in Iași). A county that does not fit the city is a data
        error (2% of the partners of a large database: "Sibiu" in Timiș) and is ignored."""
        if not partner.state_id:
            return False
        states = self._partner_match_states(values)
        if not states or partner.state_id in states:
            return False
        return self._partner_match_is_locality(partner.city, partner.state_id) and self._partner_match_is_locality(
            values.get("city"), states
        )

    @api.model
    def _partner_match_score(self, partner, values):
        """``(score, name_score)`` of ``partner`` against ``values``, both 0..1.

        The name is compared with :func:`~.partner_match.name_similarity`; street and city weigh
        in only when both sides have them. In two counties that both have a locality of that name
        (``_partner_match_other_county``), street and city score 0: a village name exists in up
        to 23 counties ("Satu Nou"), and the same street there is another address.
        """
        scores = {"name": pm.name_similarity(partner.name, values.get("name"))}
        other_county = self._partner_match_other_county(partner, values)
        for field in ("street", "city"):
            stored, given = pm.normalize_text(partner[field]), pm.normalize_text(values.get(field))
            if stored and given:
                scores[field] = 0.0 if other_county else pm.jaccard_similarity(stored, given)
        total_weight = sum(MATCH_WEIGHTS[field] for field in scores)
        score = sum(MATCH_WEIGHTS[field] * value for field, value in scores.items()) / total_weight
        return score, scores["name"]

    @api.model
    def _partner_match_reasons(self, partner, keys, use):
        country = partner.country_id.code or "RO"
        reasons = []
        if "vat" in use and keys["vat"] and pm.normalize_vat(partner.vat) == keys["vat"]:
            reasons.append("vat")
        if "email" in use and keys["email"] and pm.normalize_email(partner.email) == keys["email"]:
            reasons.append("email")
        if "phone" in use and keys["phone_key"] and pm.phone_key(partner.phone, country) == keys["phone_key"]:
            reasons.append("phone")
        return reasons

    @api.model
    def _find_similar_partners(self, values, domain=None, keys=MATCH_KEYS, limit=20):
        """Partners that share a strong key with ``values``, scored, best first.

        ``values``: ``name``, ``vat``, ``email``, ``phone``, ``country_code`` (of the phone,
        Romania by default), ``street``, ``city``, and the county as ``state_id`` or as a code or
        name in ``county`` / ``state_code``. Candidates are selected only on the keys in
        ``keys`` (VAT, email, phone): a name alone matches every "Ion Popescu" in the database.
        ``domain`` narrows them (company, ``is_company``, ...).

        Returns a list of ``{"partner", "score", "name_score", "reasons"}``, where ``reasons`` lists
        the keys shared with ``values``. Nothing is decided here: whether the best candidate is
        reused, proposed or ignored is up to the caller.
        """
        match_keys = self._partner_match_keys(values)
        conditions = self._partner_match_conditions(match_keys, keys)
        if not conditions:
            return []
        # raw query: pending writes (phone_sanitized is a stored compute) must reach the table
        self.flush_model(
            [name for name in ("vat", "email", "email_normalized", "phone", "phone_sanitized") if name in self._fields]
        )
        self.env.cr.execute(SQL("SELECT id FROM res_partner WHERE %s", SQL(" OR ").join(conditions)))
        ids = [row[0] for row in self.env.cr.fetchall()]
        if not ids:
            return []
        candidates = self.search([*(domain or []), ("id", "in", ids)], limit=limit)
        result = []
        for partner in candidates:
            score, name_score = self._partner_match_score(partner, values)
            result.append(
                {
                    "partner": partner,
                    "score": score,
                    "name_score": name_score,
                    "reasons": self._partner_match_reasons(partner, match_keys, keys),
                }
            )
        result.sort(key=lambda item: (-item["score"], item["partner"].id))
        return result
